#!/usr/bin/env python3
"""
Seed script: populates LoanOverview DynamoDB table with fake demo records.

Usage:
    python scripts/seed_loan_overview.py [--table LoanOverview-dev] [--region us-east-1]

Defaults to table LoanOverview-dev in us-east-1. Override via CLI args or
the LOAN_OVERVIEW_TABLE / AWS_DEFAULT_REGION environment variables.
"""
import argparse
import json
import os
import boto3
from decimal import Decimal

FAKE_LOANS = [
    {
        "loan_id": "265561631",
        "guid": "4707ee03-e10d-4792-840f-eb871db8dfd4",
        "organization": "gri",
        "state": "IL",
        "loan_purpose": "Purchase",
        "base_loan_amount": Decimal("400000"),
        "buyer_names": "John A Homeowner",
        "buyer_vesting": "Joint Tenancy",
        "seller_names": "Robert B Seller",
        "property_type": "Detached",
        "property_address": "123 Maple Ave, Springfield, IL 62701",
        "property_county": "Cook",
        "parcel_number": "14-21-301-012",
        "borrower_last_name": "Homeowner",
        "loan_status": "In Progress",
        "loan_officer": "Jane Smith",
    },
    {
        "loan_id": "319847205",
        "guid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "organization": "gra",
        "state": "TX",
        "loan_purpose": "Refinance",
        "base_loan_amount": Decimal("275000"),
        "buyer_names": "Maria L Reyes",
        "buyer_vesting": "Community Property",
        "seller_names": "",
        "property_type": "Attached",
        "property_address": "456 Oak Blvd, Austin, TX 78701",
        "property_county": "Travis",
        "parcel_number": "0239-4501-0012",
        "borrower_last_name": "Reyes",
        "loan_status": "Approved",
        "loan_officer": "Carlos Mendez",
    },
    {
        "loan_id": "408823917",
        "guid": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
        "organization": "kbhs",
        "state": "CA",
        "loan_purpose": "Purchase",
        "base_loan_amount": Decimal("650000"),
        "buyer_names": "David K Park",
        "buyer_vesting": "Sole and Separate Property",
        "seller_names": "Sunrise Homes LLC",
        "property_type": "Detached",
        "property_address": "789 Sunset Dr, San Diego, CA 92101",
        "property_county": "San Diego",
        "parcel_number": "533-190-28-00",
        "borrower_last_name": "Park",
        "loan_status": "Submitted",
        "loan_officer": "Amy Chen",
    },
]


def seed(table_name: str, region: str) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    for loan in FAKE_LOANS:
        table.put_item(Item=loan)
        print(f"  Seeded loan_id={loan['loan_id']}  guid={loan['guid']}")

    print(f"\nDone — {len(FAKE_LOANS)} records written to {table_name}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed LoanOverview DynamoDB table")
    parser.add_argument(
        "--table",
        default=os.environ.get("LOAN_OVERVIEW_TABLE", "gpt-mcp-loan-overview-demo"),
        help="DynamoDB table name (default: LoanOverview-dev)",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        help="AWS region (default: us-east-1)",
    )
    args = parser.parse_args()

    print(f"Seeding table '{args.table}' in region '{args.region}' ...")
    seed(args.table, args.region)


if __name__ == "__main__":
    main()
