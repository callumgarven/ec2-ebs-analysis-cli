from mypy_boto3_ec2 import EC2Client

from ec2_ebs_analysis_cli.aws import EC2Service

def test_get_instances_with_ebs_volumes(ec2_client: EC2Client) -> None:
    """Verify EC2 instances and attached volume sizes are retrieved."""
    # Create test volume
    vol1 = ec2_client.create_volume(AvailabilityZone="eu-west-2a", Size=50)
    vol2 = ec2_client.create_volume(AvailabilityZone="eu-west-2a", Size=30)

    # Launch instance
    res = ec2_client.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "prod-web"}],
            }
        ],
    )
    instance_id = res["Instances"][0]["InstanceId"]

    # Stop instance to attach volumes in stopped state
    ec2_client.stop_instances(InstanceIds=[instance_id])

    # Attach volumes
    ec2_client.attach_volume(
        VolumeId=vol1["VolumeId"], InstanceId=instance_id, Device="/dev/xvdf"
    )
    ec2_client.attach_volume(
        VolumeId=vol2["VolumeId"], InstanceId=instance_id, Device="/dev/xvdg"
    )

    service = EC2Service(region_name="eu-west-2")
    instances = service.get_instances()

    assert len(instances) == 1
    inst = instances[0]
    assert inst.instance_id == instance_id
    assert inst.name == "prod-web"

    # 50 (vol1) + 30 (vol2) + 8 (moto default root volume) = 88 GiB
    assert inst.total_ebs_gib == 88
    assert round(inst.total_ebs_gb, 1) == 94.5

def test_server_side_name_filtering(ec2_client: EC2Client) -> None:
    """Verify server-side tag filtering returns only matching instances."""
    ec2_client.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "alpha"}],
            }
        ],
    )
    ec2_client.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "beta"}],
            }
        ],
    )

    service = EC2Service(region_name="eu-west-2")
    filtered = service.get_instances(name_filter="alpha")

    assert len(filtered) == 1
    assert filtered[0].name == "alpha"

def test_parse_instance_without_tags(ec2_client: EC2Client) -> None:
    """Verify instances lacking a Name tag default gracefully to 'None'."""
    from ec2_ebs_analysis_cli.aws import EC2Service

    # Launch an instance with no TagSpecifications
    res = ec2_client.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.micro",
        MinCount=1,
        MaxCount=1,
    )
    instance_id = res["Instances"][0]["InstanceId"]

    service = EC2Service(region_name="eu-west-2")
    instances = service.get_instances()

    assert len(instances) == 1
    assert instances[0].instance_id == instance_id
    assert instances[0].name == "None"