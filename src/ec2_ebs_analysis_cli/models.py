from dataclasses import dataclass, field
from enum import Enum

# Binary GiB (2^30 bytes) to Decimal GB (10^9 bytes) conversion ratio
# See https://www.cl.cam.ac.uk/teaching/2021/PrepCS/CompFunds/NumberSystems.html
GIB_TO_GB_MULTIPLIER: float = 1.073741824


class SortField(str, Enum):
    """Fields available for sorting."""

    EBS_SIZE = "ebs_size"
    NAME = "name"
    STATE = "state"
    ID = "id"


class SortOrder(str, Enum):
    """Direction of sort."""

    ASC = "asc"
    DESC = "desc"


class OutputFormat(str, Enum):
    """Supported output formats."""

    PLAINTEXT = "plaintext"
    JSON = "json"


@dataclass(frozen=True)
class EBSVolume:
    """Represents an attached EBS volume."""

    volume_id: str
    size_gib: int

    @property
    def size_gb(self) -> float:
        """Calculate volume size in decimal gigabytes (1 GB = 10^9 bytes)."""
        return self.size_gib * GIB_TO_GB_MULTIPLIER


@dataclass(frozen=True)
class EC2Instance:
    """Represents an EC2 instance with its metadata and attached EBS storage."""

    instance_id: str
    name: str
    private_ip: str | None
    public_ip: str | None
    instance_type: str
    state: str
    volumes: list[EBSVolume] = field(default_factory=list)

    @property
    def total_ebs_gib(self) -> int:
        """Sum of all attached volumes in GiB."""
        return sum(v.size_gib for v in self.volumes)

    @property
    def total_ebs_gb(self) -> float:
        """Sum of all attached volumes in decimal GB."""
        return sum(v.size_gb for v in self.volumes)
