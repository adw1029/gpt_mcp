#!/usr/bin/env python3
"""
Uploads the static upload.html page to the LoanDocumentsBucket.
Run once after each sam deploy.

Usage:
    python scripts/upload_static_page.py [--bucket gpt-mcp-loan-documents-dev-<account_id>] [--region us-east-2]
"""
import argparse
import os
import boto3

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, "..", "src", "static", "upload.html")


def upload(bucket: str, region: str) -> None:
    s3 = boto3.client("s3", region_name=region)
    with open(HTML_PATH, "rb") as f:
        s3.put_object(
            Bucket=bucket,
            Key="upload.html",
            Body=f.read(),
            ContentType="text/html",
        )
    print(f"Uploaded upload.html to s3://{bucket}/upload.html")
    website_url = f"http://{bucket}.s3-website.{region}.amazonaws.com/upload.html"
    print(f"Website URL: {website_url}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload static upload.html to S3")
    parser.add_argument("--bucket", required=True, help="S3 bucket name (e.g. gpt-mcp-loan-documents-dev-730784326723)")
    parser.add_argument("--region", default=os.environ.get("AWS_DEFAULT_REGION", "us-east-2"))
    args = parser.parse_args()
    upload(args.bucket, args.region)


if __name__ == "__main__":
    main()
