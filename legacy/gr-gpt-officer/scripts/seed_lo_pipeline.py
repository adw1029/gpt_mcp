#!/usr/bin/env python3
"""
Seed script: populates LoPipeline DynamoDB table with 1 demo record for Andrew Cui.
Loan IDs cross-reference the BorrowerPortal seed data.

Usage:
    python scripts/seed_lo_pipeline.py [--table gr-lo-pipeline-dev] [--region us-east-2]
"""
import argparse
import os
import boto3
from decimal import Decimal

FAKE_LO_RECORDS = [
    {
        "lo_id": "andrew-cui",
        "lo_name": "Andrew Cui",
        "team": "Conventional Purchase Team — Midwest Region",
        "loans": [
            # 1 — Active / Processing (no lock yet)
            {
                "loan_id": "501234001",
                "borrower_name": "Ryan T Chen",
                "stage": "Processing",
                "amount": Decimal("465000"),
                "state": "IL",
                "lock_expiry": None,
                "lock_days_remaining": None,
                "close_date": "2026-05-10",
                "days_to_close": Decimal("41"),
                "days_in_status": Decimal("4"),
                "open_conditions_count": Decimal("0"),
                "funded": False,
                "suspended": False,
                "compliance_alerts": ["Rate not yet locked — floating at market"],
            },
            # 2 — In Underwriting with conditions (Jamie Torres)
            {
                "loan_id": "501234002",
                "borrower_name": "Jamie Torres",
                "stage": "Underwriting",
                "amount": Decimal("310000"),
                "state": "OH",
                "lock_expiry": "2026-04-19",
                "lock_days_remaining": Decimal("20"),
                "close_date": "2026-04-18",
                "days_to_close": Decimal("19"),
                "days_in_status": Decimal("5"),
                "open_conditions_count": Decimal("3"),
                "funded": False,
                "suspended": False,
                "compliance_alerts": [],
            },
            # 3 — Conditional Approval, CD not yet sent
            {
                "loan_id": "501234003",
                "borrower_name": "James R Kowalski",
                "stage": "Conditional Approval",
                "amount": Decimal("390000"),
                "state": "MI",
                "lock_expiry": "2026-04-14",
                "lock_days_remaining": Decimal("15"),
                "close_date": "2026-04-11",
                "days_to_close": Decimal("12"),
                "days_in_status": Decimal("3"),
                "open_conditions_count": Decimal("2"),
                "funded": False,
                "suspended": False,
                "compliance_alerts": ["CD not yet sent — closing in 12 days"],
            },
            # 4 — Clear to Close, lock expiring soon
            {
                "loan_id": "501234004",
                "borrower_name": "Angela S Kim",
                "stage": "Clear to Close",
                "amount": Decimal("525000"),
                "state": "IL",
                "lock_expiry": "2026-04-05",
                "lock_days_remaining": Decimal("6"),
                "close_date": "2026-04-04",
                "days_to_close": Decimal("5"),
                "days_in_status": Decimal("1"),
                "open_conditions_count": Decimal("0"),
                "funded": False,
                "suspended": False,
                "compliance_alerts": ["⚠️ Rate lock expires in 6 days — confirm closing is on track"],
            },
            # 5 — Funded / closed this week
            {
                "loan_id": "501234005",
                "borrower_name": "Derek T Nguyen",
                "stage": "Funded",
                "amount": Decimal("285000"),
                "state": "IN",
                "lock_expiry": "2026-03-31",
                "lock_days_remaining": Decimal("2"),
                "close_date": "2026-03-25",
                "days_to_close": Decimal("0"),
                "days_in_status": Decimal("0"),
                "open_conditions_count": Decimal("0"),
                "funded": True,
                "suspended": False,
                "compliance_alerts": [],
            },
        ],
        "analytics": {
            "volume_this_month_dollars": Decimal("3215000"),
            "volume_this_month_count": Decimal("8"),
            "volume_last_month_dollars": Decimal("2780000"),
            "volume_last_month_count": Decimal("6"),
            "pull_through_rate_pct": "76.8",
            "avg_loan_size_90d": Decimal("375400"),
            "avg_days_to_close": Decimal("36"),
            "leads_this_week": Decimal("5"),
            "applications_this_week": Decimal("4"),
            "refi_eligible_count": Decimal("1"),
            "product_mix": {
                "Conventional 30yr": "70%",
                "Conventional 15yr": "15%",
                "FHA 30yr": "10%",
                "VA 30yr": "5%",
            },
            "fallout_by_type": [
                {"type": "Conventional", "reason": "Borrower found another lender", "count": Decimal("1")},
                {"type": "FHA", "reason": "DTI exceeded limit", "count": Decimal("1")},
            ],
            "top_referrals": [
                {"source": "Keller Williams Chicago North — Agent Dan Park", "volume_ytd": Decimal("4650000"), "count": Decimal("9")},
                {"source": "Century 21 Detroit Metro", "volume_ytd": Decimal("1920000"), "count": Decimal("4")},
                {"source": "Past Client Referrals", "volume_ytd": Decimal("850000"), "count": Decimal("3")},
            ],
        },
    },
]


def seed(table_name: str, region: str) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    # Purge all existing records before re-seeding to avoid stale data
    print("  Scanning for existing records to purge...")
    scan = table.scan(ProjectionExpression="lo_id")
    existing_ids = [item["lo_id"] for item in scan.get("Items", [])]
    desired_ids = {r["lo_id"] for r in FAKE_LO_RECORDS}
    stale_ids = [lo_id for lo_id in existing_ids if lo_id not in desired_ids]

    for lo_id in stale_ids:
        table.delete_item(Key={"lo_id": lo_id})
        print(f"  Deleted stale lo_id={lo_id}")

    for record in FAKE_LO_RECORDS:
        table.put_item(Item=record)
        loan_count = len(record.get("loans", []))
        print(f"  Seeded lo_id={record['lo_id']}  name={record['lo_name']}  loans={loan_count}")

    print(f"\nDone — {len(FAKE_LO_RECORDS)} LO record written to {table_name}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed LoPipeline DynamoDB table")
    parser.add_argument(
        "--table",
        default=os.environ.get("LO_PIPELINE_TABLE", "gr-lo-pipeline-dev"),
        help="DynamoDB table name (default: gr-lo-pipeline-dev)",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_DEFAULT_REGION", "us-east-2"),
        help="AWS region (default: us-east-2)",
    )
    args = parser.parse_args()

    print(f"Seeding table '{args.table}' in region '{args.region}' ...")
    seed(args.table, args.region)


if __name__ == "__main__":
    main()
