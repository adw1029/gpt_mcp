#!/usr/bin/env python3
"""
Seed script: populates ClientProfile DynamoDB table with demo records.

Usage:
    python scripts/seed_client_profiles.py [--table gpt-mcp-client-profile-dev] [--region us-east-2]
"""
import argparse
import os
import boto3
from decimal import Decimal

FAKE_PROFILES = [
    {
        "borrower_id": "rivera-alex-t",
        "loan_id": "123456789",
        "guid": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "borrower_first_name": "Alex",
        "borrower_last_name": "Rivera",
        "personal_background": (
            "Alex is a marketing director at a regional healthcare company in Scottsdale, AZ. "
            "First-time homebuyer purchasing a detached single-family home. Very responsive "
            "and comes well-prepared with documentation. Prefers phone calls over email. "
            "Strong W-2 income history, no gaps in employment over the past 7 years. "
            "Good credit with one older derogatory mark that has since been resolved."
        ),
        "loan_history": [
            {
                "loan_id": "123456789",
                "purpose": "Purchase",
                "amount": Decimal("320000"),
                "status": "In Progress",
                "property_address": "55 Cactus Rd, Scottsdale, AZ 85251",
                "year": 2025,
            }
        ],
        "reviews": [
            {
                "reviewer": "Jane Smith",
                "rating": Decimal("5"),
                "comment": (
                    "Alex was extremely easy to work with. All docs were submitted ahead of "
                    "schedule and he followed up proactively. Would absolutely work with him again."
                ),
                "date": "2025-02-10",
                "tags": ["organized", "proactive", "responsive"],
            },
            {
                "reviewer": "Tom Nguyen",
                "rating": Decimal("4"),
                "comment": (
                    "Great borrower overall. The older derogatory mark needed a written "
                    "explanation letter but Alex handled it quickly with no pushback."
                ),
                "date": "2025-01-28",
                "tags": ["cooperative", "first-time-buyer"],
            },
        ],
        "overall_rating": "4.5",
    },
    {
        "borrower_id": "homeowner-john-a",
        "loan_id": "265561631",
        "guid": "4707ee03-e10d-4792-840f-eb871db8dfd4",
        "borrower_first_name": "John",
        "borrower_last_name": "Homeowner",
        "personal_background": (
            "John is a software engineer based in Springfield, IL with 12 years of stable "
            "employment at a mid-sized tech firm. He is purchasing his first home with his "
            "spouse. Very detail-oriented and asks thorough questions during the process. "
            "Prefers email communication and responds within a few hours. Has excellent credit "
            "history with no derogatory marks."
        ),
        "loan_history": [
            {
                "loan_id": "265561631",
                "purpose": "Purchase",
                "amount": Decimal("400000"),
                "status": "In Progress",
                "property_address": "123 Maple Ave, Springfield, IL 62701",
                "year": 2024,
            }
        ],
        "reviews": [
            {
                "reviewer": "Jane Smith",
                "rating": Decimal("5"),
                "comment": (
                    "John was an absolute pleasure to work with. Came fully prepared with all "
                    "documents on day one. Zero follow-up needed on missing items. Would love "
                    "to work with him again."
                ),
                "date": "2024-11-15",
                "tags": ["organized", "responsive", "prepared"],
            },
            {
                "reviewer": "Carlos Mendez",
                "rating": Decimal("4"),
                "comment": (
                    "Great borrower overall. Asked a lot of questions upfront which slowed "
                    "things a bit, but once he understood the process he was very smooth to "
                    "work with. Strong financials."
                ),
                "date": "2024-10-30",
                "tags": ["thorough", "strong-financials"],
            },
        ],
        "overall_rating": "4.5",
    },
    {
        "borrower_id": "reyes-maria-l",
        "loan_id": "319847205",
        "guid": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "borrower_first_name": "Maria",
        "borrower_last_name": "Reyes",
        "personal_background": (
            "Maria is a licensed nurse practitioner in Austin, TX refinancing her primary "
            "residence to consolidate debt and lower her monthly payments. Self-employed "
            "through her own practice for the past 4 years — income documentation required "
            "extra attention. Very communicative and proactive. Spanish-speaking borrower "
            "who appreciates bilingual support when available."
        ),
        "loan_history": [
            {
                "loan_id": "319847205",
                "purpose": "Refinance",
                "amount": Decimal("275000"),
                "status": "Approved",
                "property_address": "456 Oak Blvd, Austin, TX 78701",
                "year": 2024,
            },
            {
                "loan_id": "204113987",
                "purpose": "Purchase",
                "amount": Decimal("210000"),
                "status": "Closed",
                "property_address": "456 Oak Blvd, Austin, TX 78701",
                "year": 2019,
            },
        ],
        "reviews": [
            {
                "reviewer": "Amy Chen",
                "rating": Decimal("4"),
                "comment": (
                    "Maria was very engaged throughout. Self-employment docs took a few extra "
                    "rounds but she was always quick to respond. Happy with the outcome."
                ),
                "date": "2024-09-20",
                "tags": ["responsive", "self-employed", "communicative"],
            },
            {
                "reviewer": "Jane Smith",
                "rating": Decimal("5"),
                "comment": (
                    "Worked with Maria on her original purchase back in 2019. One of the best "
                    "borrowers I've had — organized, patient, and very pleasant to deal with."
                ),
                "date": "2019-06-12",
                "tags": ["organized", "pleasant", "repeat-client"],
            },
            {
                "reviewer": "Tom Nguyen",
                "rating": Decimal("3"),
                "comment": (
                    "Income verification for her practice took longer than expected and "
                    "required multiple document requests. Not difficult, just complex. "
                    "Recommend flagging self-employment early."
                ),
                "date": "2024-08-05",
                "tags": ["complex-income", "self-employed"],
            },
        ],
        "overall_rating": "4.0",
    },
    {
        "borrower_id": "park-david-k",
        "loan_id": "408823917",
        "guid": "f9e8d7c6-b5a4-3210-fedc-ba9876543210",
        "borrower_first_name": "David",
        "borrower_last_name": "Park",
        "personal_background": (
            "David is a software architect at a Fortune 500 company in San Diego, CA. "
            "Purchasing a new construction home from Sunrise Homes LLC as his primary "
            "residence. High income, high assets, and a pristine credit profile. Very "
            "busy schedule — prefers concise communication and makes quick decisions. "
            "Has worked with multiple lenders in the past and knows the process well."
        ),
        "loan_history": [
            {
                "loan_id": "408823917",
                "purpose": "Purchase",
                "amount": Decimal("650000"),
                "status": "Submitted",
                "property_address": "789 Sunset Dr, San Diego, CA 92101",
                "year": 2024,
            },
            {
                "loan_id": "301556742",
                "purpose": "Purchase",
                "amount": Decimal("480000"),
                "status": "Closed",
                "property_address": "22 Harbor View Ln, San Diego, CA 92103",
                "year": 2020,
            },
        ],
        "reviews": [
            {
                "reviewer": "Amy Chen",
                "rating": Decimal("5"),
                "comment": (
                    "David is a dream borrower. Everything submitted on time, perfect docs, "
                    "no drama. Just keep communications short and factual — he doesn't need "
                    "hand-holding. Highly recommended."
                ),
                "date": "2024-12-01",
                "tags": ["organized", "efficient", "experienced"],
            },
            {
                "reviewer": "Carlos Mendez",
                "rating": Decimal("4"),
                "comment": (
                    "Smooth process. David is experienced and expects things to move fast — "
                    "make sure your team is ready to keep pace. No issues at all."
                ),
                "date": "2020-03-18",
                "tags": ["experienced", "fast-paced"],
            },
        ],
        "overall_rating": "4.5",
    },
]


def seed(table_name: str, region: str) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    for profile in FAKE_PROFILES:
        table.put_item(Item=profile)
        print(f"  Seeded borrower_id={profile['borrower_id']}  name={profile['borrower_first_name']} {profile['borrower_last_name']}")

    print(f"\nDone — {len(FAKE_PROFILES)} records written to {table_name}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed ClientProfile DynamoDB table")
    parser.add_argument(
        "--table",
        default=os.environ.get("CLIENT_PROFILE_TABLE", "gpt-mcp-client-profile-dev"),
        help="DynamoDB table name (default: gpt-mcp-client-profile-dev)",
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
