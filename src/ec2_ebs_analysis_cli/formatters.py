import json
from typing import Any
from ec2_ebs_analysis_cli.models import EC2Instance

def format_plaintext(instances: list[EC2Instance]) -> str:
    """Format instances into aligned columns using matrix transposition."""
    if not instances:
        return "No instances found.\nTotal EBS Volume Size: 0.0 GB"

    # Build string representation of all rows
    rows = [
        (
            i.instance_id,
            i.name,
            str(i.private_ip),
            str(i.public_ip),
            i.instance_type,
            i.state,
            f"{i.total_ebs_gb:.1f}"
        )
        for i in instances
    ]

    # Calculate max width per column (zip(*rows) transposes the matrix)
    widths = [max(len(item) for item in col) for col in zip(*rows)]

    # Format lines using dynamic f-string padding
    lines = ["  ".join(f"{val:<{w}}" for val, w in zip(row, widths)) for row in rows]

    total_gb = sum(i.total_ebs_gb for i in instances)
    lines.append(f"Total EBS Volume Size: {total_gb:.1f} GB")

    return "\n".join(lines)

def format_json(instances: list[EC2Instance]) -> str:
    """Format instances and summary metrics as valid JSON."""
    payload: dict[str, Any] = {
        "instances": [
            {
                "instance_id": i.instance_id,
                "name": i.name,
                "private_ip": i.private_ip,
                "public_ip": i.public_ip,
                "instance_type": i.instance_type,
                "state": i.state,
                "total_ebs_size_gb": round(i.total_ebs_gb, 1),
                "volumes": [{"id": v.volume_id, "size_gb": round(v.size_gb, 1)} for v in i.volumes],
            }
            for i in instances
        ],
        "summary": {
            "instance_count": len(instances),
            "total_ebs_size_gb": round(sum(i.total_ebs_gb for i in instances), 1),
        },
    }
    return json.dumps(payload, indent=2)