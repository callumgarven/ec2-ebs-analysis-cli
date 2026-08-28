import json

from ec2_ebs_analysis_cli.formatters import format_json, format_plaintext
from ec2_ebs_analysis_cli.models import EBSVolume, EC2Instance


def test_ebs_volume_conversion_math() -> None:
    """Verify 100 GiB converts to ~107.4 decimal GB (1 GiB = 1.073741824 GB)."""
    v1 = EBSVolume(volume_id="vol-1", size_gib=10)
    v2 = EBSVolume(volume_id="vol-2", size_gib=30)
    v3 = EBSVolume(volume_id="vol-3", size_gib=60)

    instance = EC2Instance(
        instance_id="i-0bdaf76758476674653",
        name="john",
        private_ip="192.168.0.1",
        public_ip=None,
        instance_type="t2.micro",
        state="stopped",
        volumes=[v1, v2, v3],
    )

    assert instance.total_ebs_gib == 100
    assert round(instance.total_ebs_gb, 1) == 107.4


def test_format_plaintext_output() -> None:
    """Test plaintext formatting against expected table structure."""
    instance = EC2Instance(
        instance_id="i-0bdaf76758476674653",
        name="john",
        private_ip="192.168.0.1",
        public_ip=None,
        instance_type="t2.micro",
        state="stopped",
        volumes=[EBSVolume(volume_id="vol-1", size_gib=100)],
    )

    output = format_plaintext([instance])
    lines = output.strip().split("\n")

    assert len(lines) == 2
    assert "i-0bdaf76758476674653" in lines[0]
    assert "john" in lines[0]
    assert "192.168.0.1" in lines[0]
    assert "None" in lines[0]
    assert "t2.micro" in lines[0]
    assert "stopped" in lines[0]
    assert "107.4" in lines[0]
    assert lines[1] == "Total EBS Volume Size: 107.4 GB"


def test_format_json_output() -> None:
    """Test JSON formatting output structure."""
    instance = EC2Instance(
        instance_id="i-12345",
        name="es-node-1",
        private_ip="10.0.0.10",
        public_ip="54.200.1.1",
        instance_type="m5.large",
        state="running",
        volumes=[EBSVolume(volume_id="vol-abc", size_gib=50)],
    )

    output = format_json([instance])
    data = json.loads(output)

    assert data["summary"]["instance_count"] == 1
    assert data["summary"]["total_ebs_size_gb"] == 53.7
    assert data["instances"][0]["name"] == "es-node-1"
    assert data["instances"][0]["public_ip"] == "54.200.1.1"
    assert data["instances"][0]["volumes"][0]["id"] == "vol-abc"


def test_format_plaintext_empty_state() -> None:
    """Verify the formatter handles empty lists without raising max() ValueError."""
    from ec2_ebs_analysis_cli.formatters import format_plaintext

    output = format_plaintext([])
    lines = output.split("\n")

    assert "No instances found." in lines[0]
    assert "Total EBS Volume Size: 0.0 GB" in lines[1]
