from mypy_boto3_ec2 import EC2Client
from typer.testing import CliRunner

from ec2_ebs_analysis_cli.cli import app

runner = CliRunner()


def test_cli_help() -> None:
    """Verify --help returns expected usage instructions."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Inspect EC2 instances" in result.output
    assert "--name" in result.output
    assert "--format" in result.output
    assert "--sort-by" in result.output


def test_cli_execution_and_sorting(ec2_client: EC2Client) -> None:
    """Verify full CLI execution with client-side sorting."""
    # Instance A with 10 GiB
    v1 = ec2_client.create_volume(AvailabilityZone="eu-west-2a", Size=10)
    res1 = ec2_client.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.nano",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "server-small"}],
            }
        ],
    )
    id1 = res1["Instances"][0]["InstanceId"]
    ec2_client.stop_instances(InstanceIds=[id1])
    ec2_client.attach_volume(
        VolumeId=v1["VolumeId"], InstanceId=id1, Device="/dev/xvdf"
    )

    # Instance B with 100 GiB
    v2 = ec2_client.create_volume(AvailabilityZone="eu-west-2a", Size=100)
    res2 = ec2_client.run_instances(
        ImageId="ami-12345678",
        InstanceType="t2.large",
        MinCount=1,
        MaxCount=1,
        TagSpecifications=[
            {
                "ResourceType": "instance",
                "Tags": [{"Key": "Name", "Value": "server-large"}],
            }
        ],
    )
    id2 = res2["Instances"][0]["InstanceId"]
    ec2_client.stop_instances(InstanceIds=[id2])
    ec2_client.attach_volume(
        VolumeId=v2["VolumeId"], InstanceId=id2, Device="/dev/xvdf"
    )

    # Run default (asc by EBS size)
    result = runner.invoke(app, ["--region", "eu-west-2"])
    assert result.exit_code == 0
    lines = result.output.strip().split("\n")
    assert "server-small" in lines[0]
    assert "server-large" in lines[1]

    # server-small (10+8) + server-large (100+8) = 126 GiB = 135.3 GB
    assert "Total EBS Volume Size: 135.3 GB" in lines[2]

    # Run descending sort
    result_desc = runner.invoke(app, ["--sort-order", "desc"])
    assert result_desc.exit_code == 0
    lines_desc = result_desc.output.strip().split("\n")
    assert "server-large" in lines_desc[0]
    assert "server-small" in lines_desc[1]

    # Run JSON format
    result_json = runner.invoke(app, ["--format", "json"])
    assert result_json.exit_code == 0
    assert '"total_ebs_size_gb": 135.3' in result_json.output
