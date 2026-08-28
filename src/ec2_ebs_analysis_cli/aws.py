from typing import TYPE_CHECKING, Any

import boto3

from ec2_ebs_analysis_cli.models import EBSVolume, EC2Instance

if TYPE_CHECKING:
    from mypy_boto3_ec2 import EC2Client
    from mypy_boto3_ec2.type_defs import FilterTypeDef, InstanceTypeDef

class EC2Service:
    """Encapsulates AWS EC2 API interactions."""

    def __init__(self, region_name: str) -> None:
        self.region_name = region_name
        self.client: EC2Client = boto3.client("ec2", region_name=region_name)

    def get_instances(self, name_filter: str | None = None) -> list[EC2Instance]:
        """Fetch EC2 instances using server-side filtering when a name is provided."""
        filters: list[FilterTypeDef] = []
        if name_filter:
            filters.append({"Name": "tag:Name", "Values": [name_filter]})

        paginator = self.client.get_paginator("describe_instances")
        page_iterator = paginator.paginate(Filters=filters) if filters else paginator.paginate()

        raw_instances: list[InstanceTypeDef] = []
        volume_ids: set[str] = set()

        for page in page_iterator:
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    raw_instances.append(instance)
                    for mapping in instance.get("BlockDeviceMappings", []):
                        ebs = mapping.get("Ebs")
                        if ebs and "VolumeId" in ebs:
                            volume_ids.add(ebs["VolumeId"])

        volume_size_map = self._get_volume_sizes(list(volume_ids))
        return [self._parse_instance(inst, volume_size_map) for inst in raw_instances]

    def _get_volume_sizes(self, volume_ids: list[str]) -> dict[str, int]:
        """Query EBS volume sizes in GiB in batches."""
        if not volume_ids:
            return {}

        volume_size_map: dict[str, int] = {}

        # Describe volumes in chunks of 200
        # See https://docs.aws.amazon.com/boto3/latest/reference/services/ec2/client/describe_volumes.html
        # https://docs.aws.amazon.com/ec2/latest/devguide/Query-Requests.html#api-pagination
        chunk_size = 200
        for i in range(0, len(volume_ids), chunk_size):
            chunk = volume_ids[i : i + chunk_size]
            response = self.client.describe_volumes(VolumeIds=chunk)
            for vol in response.get("Volumes", []):
                volume_size_map[vol["VolumeId"]] = vol.get("Size", 0)

        return volume_size_map

    def _parse_instance(
        self, instance_data: dict[str, Any], volume_size_map: dict[str, int]
    ) -> EC2Instance:
        """Parse raw EC2 instance dictionary into model."""
        instance_id = instance_data.get("InstanceId", "unknown")
        instance_type = instance_data.get("InstanceType", "unknown")
        state = instance_data.get("State", {}).get("Name", "unknown")
        private_ip = instance_data.get("PrivateIpAddress")
        public_ip = instance_data.get("PublicIpAddress")

        # Extract Name tag
        name = "None"
        for tag in instance_data.get("Tags", []):
            if tag.get("Key") == "Name":
                name = tag.get("Value", "None")
                break

        # Map attached volumes
        volumes: list[EBSVolume] = []
        for mapping in instance_data.get("BlockDeviceMappings", []):
            ebs = mapping.get("Ebs")
            if ebs and "VolumeId" in ebs:
                vol_id = ebs["VolumeId"]
                size_gib = volume_size_map.get(vol_id, 0)
                volumes.append(EBSVolume(volume_id=vol_id, size_gib=size_gib))

        return EC2Instance(
            instance_id=instance_id,
            name=name,
            private_ip=private_ip,
            public_ip=public_ip,
            instance_type=instance_type,
            state=state,
            volumes=volumes,
        )

    def start_instances(self, instance_ids: list[str]) -> list[str]:
        """Start stopped instances."""
        if not instance_ids:
            return []
        self.client.start_instances(InstanceIds=instance_ids)
        return instance_ids