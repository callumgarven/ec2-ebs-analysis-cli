import os
from collections.abc import Generator

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_ec2 import EC2Client


@pytest.fixture(autouse=True)
def block_real_aws_credentials() -> None:
    """Ensure boto3 cannot accidentally access real AWS credentials."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"

    # Remove config file references
    os.environ["AWS_SHARED_CREDENTIALS_FILE"] = os.devnull
    os.environ["AWS_CONFIG_FILE"] = os.devnull

    # Ensure AWS_PROFILE is not set
    os.environ.pop("AWS_PROFILE", None)


@pytest.fixture
def ec2_client(block_real_aws_credentials: None) -> Generator[EC2Client]:
    """Provide a Moto-mocked EC2 client."""

    with mock_aws():
        client = boto3.client("ec2", region_name="eu-west-2")
        yield client
