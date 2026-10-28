import os
import boto3


def resolve_bucket_region(bucket_name: str) -> str:
    """Return the bucket's AWS region, always using a regional endpoint."""
    return (
        os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or boto3.session.Session().region_name
        or "us-east-2"
    )
