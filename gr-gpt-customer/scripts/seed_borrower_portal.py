#!/usr/bin/env python3
"""
Seed script: populates BorrowerPortal DynamoDB table with 5 demo records
for Andrew Cui's pipeline (LO).

Usage:
    python scripts/seed_borrower_portal.py [--table gr-borrower-portal-dev] [--region us-east-2]
"""
import argparse
import os
import boto3
from decimal import Decimal

FAKE_PORTAL_RECORDS = [
    {
        "loan_id": "501234001",
        "borrower_name": "Ryan T Chen",
        "loan_stage": "Processing",
        "stage_number": Decimal("2"),
        "uw_decision": "None",
        "assigned_underwriter": "Not yet assigned",
        "open_conditions": [],
        "recent_updates": [
            {"date": "2026-03-27", "description": "Appraisal ordered through ServiceLink AMC — inspection Apr 8"},
            {"date": "2026-03-26", "description": "Loan Estimate sent via e-sign"},
            {"date": "2026-03-25", "description": "Application accepted — processing team review started"},
        ],
        "rate_lock": {
            "rate": None, "apr": None, "lock_date": None, "expiry_date": None,
            "days_remaining": Decimal("0"), "confirmed": False,
            "lock_period_days": Decimal("0"), "extension_cost_points": None,
            "extension_cost_dollars": None, "float_down_available": False,
            "float_down_rate": None, "program_switch_eligible": True,
        },
        "closing": {
            "date": "2026-05-10", "time": "TBD",
            "location": "Chicago Title, 55 W Monroe St, Chicago, IL 60603",
            "attorney": None, "title_company": "Chicago Title",
            "cash_to_close": None, "cd_sent_date": None, "cd_acknowledged": False,
            "cd_acknowledged_at": None, "ctc_issued": False, "funded": False,
            "funded_at": None, "wire_confirmed": False, "wire_amount": None,
            "deed_recording_status": "Pending", "first_payment_date": "2026-07-01",
            "accepted_payment_methods": "Cashier's check or wire transfer",
        },
        "appraisal": {
            "status": "Inspection Scheduled", "amc": "ServiceLink AMC",
            "ordered_date": "2026-03-27", "inspection_date": "2026-04-08",
            "inspection_time": "2:00 PM", "report_received_date": None,
            "value": None, "ltv": None, "meets_purchase_price": None,
            "waiver_approved": False, "flagged": False, "flag_reason": None,
            "flood_zone": "Zone X — standard flood insurance not required",
        },
        "escrow": {
            "pmi_required": True, "pmi_monthly": Decimal("168"),
            "pmi_removal_ltv": "78", "pmi_years_estimate": "7",
            "monthly_escrow": Decimal("398"), "property_tax_monthly": Decimal("254"),
            "hoi_monthly": Decimal("144"), "hoi_verified": False,
            "hoi_carrier": "Pending", "flood_insurance_required": False,
        },
        "servicing": {
            "first_payment_date": "2026-07-01",
            "servicer": "TBD — determined at closing", "autopay_link": None,
            "transfer_pending": False, "transfer_servicer": None,
            "transfer_effective_date": None, "refi_savings_monthly": Decimal("0"),
            "refi_rate_available": None,
        },
        "loan_officer": {
            "name": "Andrew Cui", "phone": "(312) 555-0198", "email": "andrew.cui@rate.com",
            "calendar_link": "https://calendly.com/andrew-cui-rate",
            "upload_portal_link": None,
            "escalation_contact": "Regional Manager: Tom Nguyen — (312) 555-0199",
        },
        "compliance": {
            "le_sent_date": "2026-03-26", "cd_sent_date": None, "trid_window_ok": True,
            "trid_days_remaining": None, "respa_flags": [], "right_of_rescission_expiry": None,
            "hmda_flags": [], "fair_lending_gaps": [],
            "disclosure_audit_trail": [
                {"date": "2026-03-26", "document": "Loan Estimate", "action": "Sent to borrower via e-sign"},
            ],
        },
        "credit_score": Decimal("738"), "credit_inquiries_90d": Decimal("1"),
        "co_borrowers": [{"name": "Lisa T Chen", "role": "Co-borrower / Spouse"}],
        "documents_submitted": ["2024 + 2023 W-2s", "30-day pay stubs", "2-month bank statements", "Purchase agreement"],
        "documents_missing": ["HOI declaration page"],
        "voe_status": "Written VOE completed — confirmed by employer March 26.",
        "voi_status": "Income verified via W-2 and pay stubs.",
        "prior_applications": [], "pricing_exceptions": [],
    },
    {
        "loan_id": "501234002",
        "borrower_name": "Jamie Torres",
        "loan_stage": "Underwriting",
        "stage_number": Decimal("3"),
        "uw_decision": "Conditional",
        "assigned_underwriter": "James T. — Conventional Central Team",
        "open_conditions": [
            {
                "id": "C001", "description": "12-month gift letter — down payment gift from parents",
                "type": "PTD", "status": "Outstanding", "deadline": "2026-04-10",
                "notes": "Signed gift letter required with donor bank statement showing availability",
                "accepted_date": None,
            },
            {
                "id": "C002", "description": "Updated bank statement — October through December",
                "type": "PTD", "status": "Outstanding", "deadline": "2026-04-10",
                "notes": "Most recent 2-month statement required — October statement is outdated",
                "accepted_date": None,
            },
            {
                "id": "C003", "description": "HOA certification letter",
                "type": "PTD", "status": "In Review", "deadline": "2026-04-10",
                "notes": "HOA cert received — underwriting review in progress",
                "accepted_date": None,
            },
        ],
        "recent_updates": [
            {"date": "2026-03-28", "description": "Conditional Approval expected within 2 business days — UW review 60% complete"},
            {"date": "2026-03-27", "description": "HOA certification received — forwarded to underwriting"},
            {"date": "2026-03-26", "description": "File submitted to underwriting"},
            {"date": "2026-03-24", "description": "Appraisal accepted — value $318,000, meets contract price"},
        ],
        "rate_lock": {
            "rate": "6.750", "apr": "6.925", "lock_date": "2026-03-20",
            "expiry_date": "2026-04-19", "days_remaining": Decimal("20"),
            "confirmed": True, "lock_period_days": Decimal("30"),
            "extension_cost_points": "0.125", "extension_cost_dollars": "388",
            "float_down_available": False, "float_down_rate": None,
            "program_switch_eligible": False,
        },
        "closing": {
            "date": "2026-04-18", "time": "11:00 AM",
            "location": "Ohio Title Services, 100 E Broad St, Columbus, OH 43215",
            "attorney": None, "title_company": "Ohio Title Services",
            "cash_to_close": Decimal("15600"), "cd_sent_date": None,
            "cd_acknowledged": False, "cd_acknowledged_at": None, "ctc_issued": False,
            "funded": False, "funded_at": None, "wire_confirmed": False,
            "wire_amount": None, "deed_recording_status": "Pending",
            "first_payment_date": "2026-06-01",
            "accepted_payment_methods": "Cashier's check or wire transfer",
        },
        "appraisal": {
            "status": "Accepted", "amc": "First American AMC",
            "ordered_date": "2026-03-10", "inspection_date": "2026-03-17",
            "inspection_time": "10:00 AM", "report_received_date": "2026-03-22",
            "value": Decimal("318000"), "ltv": "94.7", "meets_purchase_price": True,
            "waiver_approved": False, "flagged": False, "flag_reason": None,
            "flood_zone": "Zone X — standard flood insurance not required",
        },
        "escrow": {
            "pmi_required": True, "pmi_monthly": Decimal("145"),
            "pmi_removal_ltv": "78", "pmi_years_estimate": "7",
            "monthly_escrow": Decimal("362"), "property_tax_monthly": Decimal("217"),
            "hoi_monthly": Decimal("144"), "hoi_verified": True,
            "hoi_carrier": "Nationwide — Policy #OH-3312-774",
            "flood_insurance_required": False,
        },
        "servicing": {
            "first_payment_date": "2026-06-01",
            "servicer": "Guaranteed Rate (in-house servicing)",
            "autopay_link": "https://servicing.rate.com/autopay",
            "transfer_pending": False, "transfer_servicer": None,
            "transfer_effective_date": None, "refi_savings_monthly": Decimal("0"),
            "refi_rate_available": None,
        },
        "loan_officer": {
            "name": "Andrew Cui", "phone": "(312) 555-0198", "email": "andrew.cui@rate.com",
            "calendar_link": "https://calendly.com/andrew-cui-rate",
            "upload_portal_link": None,
            "escalation_contact": "Regional Manager: Tom Nguyen — (312) 555-0199",
        },
        "compliance": {
            "le_sent_date": "2026-03-18", "cd_sent_date": None, "trid_window_ok": True,
            "trid_days_remaining": None, "respa_flags": [], "right_of_rescission_expiry": None,
            "hmda_flags": [], "fair_lending_gaps": [],
            "disclosure_audit_trail": [
                {"date": "2026-03-18", "document": "Loan Estimate", "action": "Sent to borrower via e-sign"},
                {"date": "2026-03-18", "document": "Loan Estimate", "action": "Acknowledged by borrower"},
            ],
        },
        "credit_score": Decimal("703"), "credit_inquiries_90d": Decimal("2"),
        "co_borrowers": [],
        "documents_submitted": ["2024 + 2023 W-2s", "30-day pay stubs", "Bank statements Oct-Nov", "Purchase agreement", "HOI dec page"],
        "documents_missing": ["Updated bank statement (Dec)", "Gift letter from parents"],
        "voe_status": "Written VOE completed — March 21.",
        "voi_status": "Income verified via W-2 and pay stubs.",
        "prior_applications": [], "pricing_exceptions": [],
    },
    {
        "loan_id": "501234003",
        "borrower_name": "James R Kowalski",
        "loan_stage": "Conditional Approval",
        "stage_number": Decimal("4"),
        "uw_decision": "Conditional",
        "assigned_underwriter": "Rachel S. — Conventional Central Team",
        "open_conditions": [
            {
                "id": "C001", "description": "Final 2025 pay stub — must show year-to-date income",
                "type": "PTD", "status": "Outstanding", "deadline": "2026-04-06",
                "notes": "Most recent pay stub is from February — March pay stub now available",
                "accepted_date": None,
            },
            {
                "id": "C002", "description": "Homeowners insurance binder",
                "type": "PTD", "status": "Outstanding", "deadline": "2026-04-06",
                "notes": "HOI policy must be bound and declaration page submitted before CTC",
                "accepted_date": None,
            },
        ],
        "recent_updates": [
            {"date": "2026-03-29", "description": "Conditional Approval issued by underwriting"},
            {"date": "2026-03-28", "description": "Appraisal accepted — no issues"},
            {"date": "2026-03-26", "description": "Income documents accepted by underwriting"},
            {"date": "2026-03-24", "description": "Closing Disclosure in preparation — pending CTC"},
        ],
        "rate_lock": {
            "rate": "6.875", "apr": "7.048", "lock_date": "2026-03-15",
            "expiry_date": "2026-04-14", "days_remaining": Decimal("15"),
            "confirmed": True, "lock_period_days": Decimal("30"),
            "extension_cost_points": "0.125", "extension_cost_dollars": "488",
            "float_down_available": False, "float_down_rate": None,
            "program_switch_eligible": False,
        },
        "closing": {
            "date": "2026-04-11", "time": "1:00 PM",
            "location": "Metro Title Group, 500 Woodward Ave, Detroit, MI 48226",
            "attorney": "Kowalski & Associates (borrower's attorney)",
            "title_company": "Metro Title Group",
            "cash_to_close": Decimal("14250"), "cd_sent_date": None,
            "cd_acknowledged": False, "cd_acknowledged_at": None, "ctc_issued": False,
            "funded": False, "funded_at": None, "wire_confirmed": False,
            "wire_amount": None, "deed_recording_status": "Pending",
            "first_payment_date": "2026-06-01",
            "accepted_payment_methods": "Cashier's check or wire transfer",
        },
        "appraisal": {
            "status": "Accepted", "amc": "ServiceLink AMC",
            "ordered_date": "2026-03-08", "inspection_date": "2026-03-14",
            "inspection_time": "9:00 AM", "report_received_date": "2026-03-20",
            "value": Decimal("398000"), "ltv": "93.7", "meets_purchase_price": True,
            "waiver_approved": False, "flagged": False, "flag_reason": None,
            "flood_zone": "Zone X — standard flood insurance not required",
        },
        "escrow": {
            "pmi_required": True, "pmi_monthly": Decimal("162"),
            "pmi_removal_ltv": "78", "pmi_years_estimate": "7",
            "monthly_escrow": Decimal("441"), "property_tax_monthly": Decimal("279"),
            "hoi_monthly": Decimal("144"), "hoi_verified": False,
            "hoi_carrier": "Pending — required before CTC",
            "flood_insurance_required": False,
        },
        "servicing": {
            "first_payment_date": "2026-06-01",
            "servicer": "Guaranteed Rate (in-house servicing)",
            "autopay_link": "https://servicing.rate.com/autopay",
            "transfer_pending": False, "transfer_servicer": None,
            "transfer_effective_date": None, "refi_savings_monthly": Decimal("0"),
            "refi_rate_available": None,
        },
        "loan_officer": {
            "name": "Andrew Cui", "phone": "(312) 555-0198", "email": "andrew.cui@rate.com",
            "calendar_link": "https://calendly.com/andrew-cui-rate",
            "upload_portal_link": None,
            "escalation_contact": "Regional Manager: Tom Nguyen — (312) 555-0199",
        },
        "compliance": {
            "le_sent_date": "2026-03-13", "cd_sent_date": None, "trid_window_ok": True,
            "trid_days_remaining": None, "respa_flags": [], "right_of_rescission_expiry": None,
            "hmda_flags": [], "fair_lending_gaps": [],
            "disclosure_audit_trail": [
                {"date": "2026-03-13", "document": "Loan Estimate", "action": "Sent to borrower via e-sign"},
                {"date": "2026-03-14", "document": "Loan Estimate", "action": "Acknowledged by borrower"},
            ],
        },
        "credit_score": Decimal("726"), "credit_inquiries_90d": Decimal("1"),
        "co_borrowers": [],
        "documents_submitted": ["2024 + 2023 W-2s", "Feb pay stub", "3-month bank statements", "Purchase agreement"],
        "documents_missing": ["March pay stub (updated)", "HOI binder"],
        "voe_status": "Written VOE completed — March 16.",
        "voi_status": "Income verified via W-2. Updated pay stub pending.",
        "prior_applications": [], "pricing_exceptions": [],
    },
    {
        "loan_id": "501234004",
        "borrower_name": "Angela S Kim",
        "loan_stage": "Clear to Close",
        "stage_number": Decimal("5"),
        "uw_decision": "Approved",
        "assigned_underwriter": "David L. — Conventional Central Team",
        "open_conditions": [],
        "recent_updates": [
            {"date": "2026-03-30", "description": "Clear to Close issued — loan docs ordered"},
            {"date": "2026-03-29", "description": "All PTD and PTF conditions cleared"},
            {"date": "2026-03-28", "description": "Closing Disclosure sent via DocuSign"},
            {"date": "2026-03-28", "description": "CD acknowledged by borrower at 3:47 PM"},
        ],
        "rate_lock": {
            "rate": "6.625", "apr": "6.798", "lock_date": "2026-03-06",
            "expiry_date": "2026-04-05", "days_remaining": Decimal("6"),
            "confirmed": True, "lock_period_days": Decimal("30"),
            "extension_cost_points": "0.125", "extension_cost_dollars": "656",
            "float_down_available": False, "float_down_rate": None,
            "program_switch_eligible": False,
        },
        "closing": {
            "date": "2026-04-04", "time": "10:30 AM",
            "location": "Investors Title, 200 N LaSalle St, Chicago, IL 60601",
            "attorney": None, "title_company": "Investors Title",
            "cash_to_close": Decimal("26750"), "cd_sent_date": "2026-03-28",
            "cd_acknowledged": True, "cd_acknowledged_at": "2026-03-28T15:47:00Z",
            "ctc_issued": True, "funded": False, "funded_at": None,
            "wire_confirmed": False, "wire_amount": None,
            "deed_recording_status": "Pending", "first_payment_date": "2026-06-01",
            "accepted_payment_methods": "Cashier's check or wire transfer",
        },
        "appraisal": {
            "status": "Accepted", "amc": "First American AMC",
            "ordered_date": "2026-03-02", "inspection_date": "2026-03-08",
            "inspection_time": "11:00 AM", "report_received_date": "2026-03-14",
            "value": Decimal("535000"), "ltv": "92.5", "meets_purchase_price": True,
            "waiver_approved": False, "flagged": False, "flag_reason": None,
            "flood_zone": "Zone X — standard flood insurance not required",
        },
        "escrow": {
            "pmi_required": True, "pmi_monthly": Decimal("214"),
            "pmi_removal_ltv": "78", "pmi_years_estimate": "8",
            "monthly_escrow": Decimal("498"), "property_tax_monthly": Decimal("284"),
            "hoi_monthly": Decimal("144"), "hoi_verified": True,
            "hoi_carrier": "Allstate — Policy #IL-8821-3304",
            "flood_insurance_required": False,
        },
        "servicing": {
            "first_payment_date": "2026-06-01",
            "servicer": "Guaranteed Rate (in-house servicing)",
            "autopay_link": "https://servicing.rate.com/autopay",
            "transfer_pending": False, "transfer_servicer": None,
            "transfer_effective_date": None, "refi_savings_monthly": Decimal("0"),
            "refi_rate_available": None,
        },
        "loan_officer": {
            "name": "Andrew Cui", "phone": "(312) 555-0198", "email": "andrew.cui@rate.com",
            "calendar_link": "https://calendly.com/andrew-cui-rate",
            "upload_portal_link": None,
            "escalation_contact": "Regional Manager: Tom Nguyen — (312) 555-0199",
        },
        "compliance": {
            "le_sent_date": "2026-03-04", "cd_sent_date": "2026-03-28", "trid_window_ok": True,
            "trid_days_remaining": Decimal("3"), "respa_flags": [],
            "right_of_rescission_expiry": None, "hmda_flags": [], "fair_lending_gaps": [],
            "disclosure_audit_trail": [
                {"date": "2026-03-04", "document": "Loan Estimate", "action": "Sent to borrower via e-sign"},
                {"date": "2026-03-05", "document": "Loan Estimate", "action": "Acknowledged by borrower"},
                {"date": "2026-03-28", "document": "Closing Disclosure", "action": "Sent to borrower via DocuSign"},
                {"date": "2026-03-28", "document": "Closing Disclosure", "action": "Acknowledged by borrower at 3:47 PM"},
            ],
        },
        "credit_score": Decimal("761"), "credit_inquiries_90d": Decimal("1"),
        "co_borrowers": [{"name": "Daniel W Kim", "role": "Co-borrower / Spouse"}],
        "documents_submitted": [
            "2024 + 2023 W-2s", "60-day pay stubs", "3-month bank statements",
            "Purchase agreement", "HOI declaration page",
        ],
        "documents_missing": [],
        "voe_status": "Written VOE completed — March 7.",
        "voi_status": "Income fully verified.",
        "prior_applications": [
            {"loan_id": "488201345", "year": 2021, "purpose": "Purchase", "status": "Closed", "amount": Decimal("320000")},
        ],
        "pricing_exceptions": [],
    },
    {
        "loan_id": "501234005",
        "borrower_name": "Derek T Nguyen",
        "loan_stage": "Funded",
        "stage_number": Decimal("7"),
        "uw_decision": "Approved",
        "assigned_underwriter": "Nicole K. — Conventional Central Team",
        "open_conditions": [],
        "recent_updates": [
            {"date": "2026-03-28", "description": "Loan funded at 2:15 PM — disbursement complete"},
            {"date": "2026-03-28", "description": "Wire of $231,500 confirmed received by Heartland Title at 1:50 PM"},
            {"date": "2026-03-27", "description": "All prior-to-funding conditions cleared — CTC issued"},
            {"date": "2026-03-25", "description": "Closing completed at Heartland Title"},
        ],
        "rate_lock": {
            "rate": "6.800", "apr": "6.972", "lock_date": "2026-03-01",
            "expiry_date": "2026-03-31", "days_remaining": Decimal("2"),
            "confirmed": True, "lock_period_days": Decimal("30"),
            "extension_cost_points": "0.125", "extension_cost_dollars": "356",
            "float_down_available": False, "float_down_rate": None,
            "program_switch_eligible": False,
        },
        "closing": {
            "date": "2026-03-25", "time": "2:00 PM",
            "location": "Heartland Title, 1 S Dearborn St, Indianapolis, IN 46201",
            "attorney": None, "title_company": "Heartland Title",
            "cash_to_close": Decimal("11820"), "cd_sent_date": "2026-03-21",
            "cd_acknowledged": True, "cd_acknowledged_at": "2026-03-21T10:22:00Z",
            "ctc_issued": True, "funded": True, "funded_at": "2026-03-28T14:15:00Z",
            "wire_confirmed": True, "wire_amount": Decimal("231500"),
            "deed_recording_status": "Recorded — Marion County, March 29, 2026",
            "first_payment_date": "2026-05-01",
            "accepted_payment_methods": "Wire transfer (completed)",
        },
        "appraisal": {
            "status": "Accepted", "amc": "ServiceLink AMC",
            "ordered_date": "2026-02-24", "inspection_date": "2026-03-02",
            "inspection_time": "10:00 AM", "report_received_date": "2026-03-08",
            "value": Decimal("292000"), "ltv": "92.3", "meets_purchase_price": True,
            "waiver_approved": False, "flagged": False, "flag_reason": None,
            "flood_zone": "Zone X — standard flood insurance not required",
        },
        "escrow": {
            "pmi_required": True, "pmi_monthly": Decimal("132"),
            "pmi_removal_ltv": "78", "pmi_years_estimate": "6",
            "monthly_escrow": Decimal("356"), "property_tax_monthly": Decimal("212"),
            "hoi_monthly": Decimal("144"), "hoi_verified": True,
            "hoi_carrier": "State Farm — Policy #IN-7741-228",
            "flood_insurance_required": False,
        },
        "servicing": {
            "first_payment_date": "2026-05-01",
            "servicer": "Guaranteed Rate (in-house servicing)",
            "autopay_link": "https://servicing.rate.com/autopay",
            "transfer_pending": False, "transfer_servicer": None,
            "transfer_effective_date": None, "refi_savings_monthly": Decimal("0"),
            "refi_rate_available": None,
        },
        "loan_officer": {
            "name": "Andrew Cui", "phone": "(312) 555-0198", "email": "andrew.cui@rate.com",
            "calendar_link": "https://calendly.com/andrew-cui-rate",
            "upload_portal_link": None,
            "escalation_contact": "Regional Manager: Tom Nguyen — (312) 555-0199",
        },
        "compliance": {
            "le_sent_date": "2026-02-27", "cd_sent_date": "2026-03-21", "trid_window_ok": True,
            "trid_days_remaining": Decimal("0"), "respa_flags": [],
            "right_of_rescission_expiry": None, "hmda_flags": [], "fair_lending_gaps": [],
            "disclosure_audit_trail": [
                {"date": "2026-02-27", "document": "Loan Estimate", "action": "Sent to borrower via e-sign"},
                {"date": "2026-02-27", "document": "Loan Estimate", "action": "Acknowledged by borrower"},
                {"date": "2026-03-21", "document": "Closing Disclosure", "action": "Sent to borrower via DocuSign"},
                {"date": "2026-03-21", "document": "Closing Disclosure", "action": "Acknowledged by borrower at 10:22 AM"},
            ],
        },
        "credit_score": Decimal("719"), "credit_inquiries_90d": Decimal("1"),
        "co_borrowers": [],
        "documents_submitted": [
            "2024 + 2023 W-2s", "30-day pay stubs", "2-month bank statements",
            "Purchase agreement", "HOI declaration page",
        ],
        "documents_missing": [],
        "voe_status": "Written VOE completed — February 28.",
        "voi_status": "Income fully verified.",
        "prior_applications": [], "pricing_exceptions": [],
    },
]


def seed(table_name: str, region: str) -> None:
    dynamodb = boto3.resource("dynamodb", region_name=region)
    table = dynamodb.Table(table_name)

    # Purge stale records not in the current seed before writing
    print("  Scanning for existing records to purge...")
    scan = table.scan(ProjectionExpression="loan_id")
    existing_ids = [item["loan_id"] for item in scan.get("Items", [])]
    desired_ids = {r["loan_id"] for r in FAKE_PORTAL_RECORDS}
    stale_ids = [loan_id for loan_id in existing_ids if loan_id not in desired_ids]

    for loan_id in stale_ids:
        table.delete_item(Key={"loan_id": loan_id})
        print(f"  Deleted stale loan_id={loan_id}")

    for record in FAKE_PORTAL_RECORDS:
        table.put_item(Item=record)
        print(f"  Seeded loan_id={record['loan_id']}  borrower={record['borrower_name']}  stage={record['loan_stage']}")

    print(f"\nDone — {len(FAKE_PORTAL_RECORDS)} records written to {table_name}.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed BorrowerPortal DynamoDB table")
    parser.add_argument(
        "--table",
        default=os.environ.get("BORROWER_PORTAL_TABLE", "gr-borrower-portal-dev"),
        help="DynamoDB table name (default: gr-borrower-portal-dev)",
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
