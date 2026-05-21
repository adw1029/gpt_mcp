import re
import uuid
import datetime
from typing import Literal
import boto3
from mcp_server.registry import mcp
from mcp_server.config import LOAN_APPLICATION_TABLE

_VIRTUAL_AGENT_URL = "https://avatar.prajnagpt.net"


def _parse_dollars(value: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except (ValueError, TypeError):
        return 0.0


def _dti_band(dti: float) -> tuple[str, str]:
    if dti < 0.36:
        return "Excellent", "Well within standard guidelines — strong approval signal."
    elif dti < 0.43:
        return "Acceptable", "Within conventional guidelines but leaves limited buffer."
    elif dti < 0.50:
        return "Elevated", "Above conventional 43% threshold; FHA or manual underwriting may be required."
    else:
        return "High", "Exceeds standard guidelines — debt reduction or larger down payment recommended."


def _ltv_band(ltv: float) -> tuple[str, str]:
    if ltv <= 0.80:
        return "Strong", "LTV ≤ 80% — no PMI required; best conventional pricing."
    elif ltv <= 0.90:
        return "Standard", "LTV 80–90% — PMI required on conventional; FHA viable."
    elif ltv <= 0.965:
        return "High leverage", "LTV 90–96.5% — FHA maximum range; conventional PMI elevated."
    else:
        return "Very high leverage", "LTV > 96.5% — exceeds FHA maximum; down payment assistance may be needed."


def _recommend_loan_type(credit_score_range: str, ltv: float, purpose: str) -> str:
    score_str = credit_score_range.lower()
    high_credit = any(x in score_str for x in ["760", "720", "700", "excellent", "very good"])
    mid_credit = any(x in score_str for x in ["680", "660", "640", "good", "fair"])
    if "va" in score_str or "veteran" in score_str:
        return "VA Loan (0% down, no PMI — if eligible)"
    if high_credit and ltv <= 0.80:
        return "Conventional (20% down — no PMI, best rate tier)"
    if high_credit and ltv <= 0.97:
        return "Conventional with PMI"
    if mid_credit or ltv > 0.80:
        return "FHA Loan (3.5% minimum down, MIP required)"
    return "FHA Loan or Conventional with PMI — review with underwriter"


def _preq_icon(preq: str) -> str:
    return {"LIKELY ELIGIBLE": "✅", "CONDITIONAL": "⚠️", "NEEDS REVIEW": "🔍"}.get(preq, "❓")


@mcp.tool()
def submit_mortgage_application(
    borrower_name: str,
    date_of_birth: str,
    property_address: str,
    property_type: Literal["Single-family", "Condo", "Townhouse", "Multi-family"],
    intended_use: Literal["Primary residence", "Second home", "Investment property"],
    loan_purpose: Literal["Purchase", "Refinance", "Cash-out Refinance"],
    purchase_price: str,
    loan_amount: str,
    employment_status: Literal["W-2 Employee", "Self-employed", "Retired", "Other"],
    annual_income: str,
    monthly_debt_payments: str,
    estimated_assets: str,
    credit_score_range: Literal["760+", "720-759", "680-719", "640-679", "600-639", "Below 600"],
) -> str:
    """
    Submit a DMX MORTGAGE (home loan) application for a residential real estate property.

    THIS IS A MORTGAGE / HOME LOAN APPLICATION ONLY. All fields relate to a real
    estate property and a home loan. Do NOT use this for auto loans, car loans,
    vehicle financing, personal loans, or student loans — those are not supported.

    IMPORTANT — do NOT call this tool until you have collected ALL 13 fields
    through conversation. Ask one question at a time, naturally. Wait for
    each answer before asking the next. Never ask about vehicles or vehicle prices.

    Collect these fields in order:
    1.  borrower_name          — full legal name (e.g. "John A. Smith")
    2.  date_of_birth          — date of birth (e.g. "March 15, 1985")
    3.  property_address       — full address of the HOME/PROPERTY being financed
    4.  property_type          — type of REAL ESTATE: Single-family, Condo, Townhouse, Multi-family
    5.  intended_use           — how borrower will use the HOME: Primary residence, Second home, Investment property
    6.  loan_purpose           — Purchase (buying a home), Refinance, or Cash-out Refinance
    7.  purchase_price         — HOME purchase price or current estimated HOME value (e.g. "$420,000")
    8.  loan_amount            — requested MORTGAGE loan amount (e.g. "$336,000")
    9.  employment_status      — W-2 Employee, Self-employed, Retired, or Other
    10. annual_income          — gross annual income before taxes (e.g. "$95,000")
    11. monthly_debt_payments  — existing monthly debts: car loans, student loans, credit cards
                                 (do NOT include the new mortgage payment — e.g. "$850")
    12. estimated_assets       — total liquid savings and checking accounts (e.g. "$45,000")
    13. credit_score_range     — approximate FICO range: 760+, 720-759, 680-719,
                                 640-679, 600-639, or Below 600

    Use this ONLY when a borrower wants to apply for a HOME LOAN or MORTGAGE, e.g.:
    - "I want to apply for a mortgage"
    - "I want to buy a home and need a loan"
    - "start a home loan / mortgage application"
    - "let's fill out a mortgage application"
    - "begin a DMX mortgage application"
    - "I want to refinance my home"

    If the borrower wants to speak with a live virtual agent instead,
    direct them to: https://avatar.prajnagpt.net

    Do NOT use this for:
    - Auto loans / car loans / vehicle financing → not supported, inform the user
    - Personal loans → not supported
    - Looking up an existing application → use get_mortgage_application_status
    """
    ddb = boto3.resource("dynamodb")
    table = ddb.Table(LOAN_APPLICATION_TABLE)
    session_id = str(uuid.uuid4())
    now = datetime.datetime.utcnow()
    ttl = int((now + datetime.timedelta(days=30)).timestamp())

    income = _parse_dollars(annual_income)
    monthly_income = income / 12 if income > 0 else 1
    existing_debts = _parse_dollars(monthly_debt_payments)
    loan_val = _parse_dollars(loan_amount)
    price_val = _parse_dollars(purchase_price)
    assets_val = _parse_dollars(estimated_assets)

    estimated_monthly_payment = loan_val * 0.00733 if loan_val > 0 else 0
    total_monthly_obligations = existing_debts + estimated_monthly_payment
    dti = total_monthly_obligations / monthly_income if monthly_income > 0 else 0
    ltv = loan_val / price_val if price_val > 0 else 0
    down_payment = price_val - loan_val if price_val > loan_val else 0
    down_pct = (down_payment / price_val * 100) if price_val > 0 else 0
    reserves_months = (assets_val / estimated_monthly_payment) if estimated_monthly_payment > 0 else 0

    dti_label, dti_detail = _dti_band(dti)
    ltv_label, ltv_detail = _ltv_band(ltv)
    loan_type_rec = _recommend_loan_type(credit_score_range, ltv, loan_purpose)

    if dti < 0.43 and ltv <= 0.97 and any(s in credit_score_range for s in ["760", "720", "680"]):
        prequalification = "LIKELY ELIGIBLE"
        preq_note = "Based on the information provided, this application meets standard eligibility criteria."
    elif dti < 0.50 and ltv <= 0.965:
        prequalification = "CONDITIONAL"
        preq_note = "Application may qualify with additional documentation or compensating factors (reserves, co-borrower, etc.)."
    else:
        prequalification = "NEEDS REVIEW"
        preq_note = "One or more factors require manual underwriter review before a determination can be made."

    item = {
        "session_id": session_id,
        "borrower_name": borrower_name,
        "borrower_name_lower": borrower_name.strip().lower(),
        "date_of_birth": date_of_birth,
        "property_address": property_address,
        "property_type": property_type,
        "intended_use": intended_use,
        "loan_purpose": loan_purpose,
        "purchase_price": purchase_price,
        "loan_amount": loan_amount,
        "employment_status": employment_status,
        "annual_income": annual_income,
        "monthly_debt_payments": monthly_debt_payments,
        "estimated_assets": estimated_assets,
        "credit_score_range": credit_score_range,
        "dti_ratio": str(round(dti, 3)),
        "ltv_ratio": str(round(ltv, 3)),
        "prequalification": prequalification,
        "status": "submitted",
        "submitted_at": now.isoformat() + "Z",
        "ttl": ttl,
    }
    table.put_item(Item=item)

    today = now.strftime("%Y%m%d")
    digit_sum = sum(int(c) for c in session_id if c.isdigit())
    suffix = str(1000 + (digit_sum % 9000)).zfill(4)
    dmx_reference = f"DMX-{today}-{suffix}"
    preq_icon = _preq_icon(prequalification)
    submitted_fmt = now.strftime("%B %d, %Y at %H:%M UTC")

    return (
        f"## 🏠 MORTGAGE APPLICATION SUBMITTED\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"### 🔖 DMX Reference: `{dmx_reference}`\n\n"
        f"**{preq_icon} Pre-Qualification: {prequalification}**  \n"
        f"_{preq_note}_\n\n"
        "---\n\n"
        "### 👤 Borrower & Property\n\n"
        "| Field | Details |\n"
        "|---|---|\n"
        f"| **Borrower** | {borrower_name} |\n"
        f"| **Date of Birth** | {date_of_birth} |\n"
        f"| **Property Address** | {property_address} |\n"
        f"| **Property Type** | {property_type} |\n"
        f"| **Intended Use** | {intended_use} |\n"
        f"| **Loan Purpose** | {loan_purpose} |\n"
        f"| **Purchase Price / Value** | {purchase_price} |\n"
        f"| **Loan Amount** | {loan_amount} |\n"
        f"| **Down Payment** | ${down_payment:,.0f} ({down_pct:.1f}%) |\n"
        f"| **Employment** | {employment_status} |\n"
        f"| **Annual Income** | {annual_income} |\n"
        f"| **Credit Score Range** | {credit_score_range} |\n"
        "\n---\n\n"
        "### 📊 Pre-Qualification Analysis\n\n"
        "| Metric | Value | Assessment |\n"
        "|---|---|---|\n"
        f"| **Est. Monthly Payment** | ${estimated_monthly_payment:,.0f} | Principal + interest (7% proxy) |\n"
        f"| **Total Monthly Obligations** | ${total_monthly_obligations:,.0f} | Including existing debts |\n"
        f"| **DTI Ratio** | **{dti:.1%}** | {dti_label} — {dti_detail} |\n"
        f"| **LTV Ratio** | **{ltv:.1%}** | {ltv_label} — {ltv_detail} |\n"
        f"| **Cash Reserves** | {reserves_months:.1f} months | Based on estimated assets |\n"
        f"| **Recommended Loan Type** | {loan_type_rec} | |\n"
        "\n---\n\n"
        "### ✅ Next Steps\n\n"
        f"1. Save your reference number: **`{dmx_reference}`**\n"
        "2. A loan officer will contact you within **1 business day** to verify your information.\n"
        "3. Gather documents: last 2 years W-2s / tax returns, 2 months pay stubs, 2 months bank statements.\n"
        "4. A hard credit pull will be performed with your authorization before final approval.\n\n"
        "---\n\n"
        f"📅 **Submitted:** {submitted_fmt}\n\n"
        f"💬 **Prefer to speak with a virtual agent?** [Chat live with our mortgage specialist]({_VIRTUAL_AGENT_URL})\n"
    )


@mcp.tool()
def get_mortgage_application_status(borrower_name: str) -> str:
    """
    Look up an existing DMX MORTGAGE application by borrower name.

    Use this when someone asks about an EXISTING mortgage application, e.g.:
    - "what is the status of Jane Doe's mortgage application?"
    - "look up the home loan application for [name]"
    - "find the DMX mortgage application for [borrower]"
    - "what was the DMX reference number for [name]?"
    - "did [name]'s mortgage application go through?"

    Do NOT use this for:
    - Starting a new application → use submit_mortgage_application
    - Loan data unrelated to a DMX application → use get_loan_overview
    """
    ddb = boto3.client("dynamodb")
    response = ddb.scan(
        TableName=LOAN_APPLICATION_TABLE,
        FilterExpression="contains(borrower_name_lower, :n)",
        ExpressionAttributeValues={":n": {"S": borrower_name.strip().lower()}},
        Limit=10,
    )
    items = response.get("Items", [])
    if not items:
        return (
            f"## ❌ Application Not Found\n\n"
            f"No DMX mortgage application found for **\"{borrower_name}\"**.\n\n"
            "If the application was just submitted, please allow a moment and try again.\n\n"
            f"💬 Need help? [Speak with our virtual mortgage agent]({_VIRTUAL_AGENT_URL})\n"
        )

    def parse_item(i):
        return {k: list(v.values())[0] for k, v in i.items()}

    parsed = [parse_item(i) for i in items]
    parsed.sort(key=lambda x: x.get("submitted_at", ""), reverse=True)
    latest = parsed[0]

    session_id = latest.get("session_id", "")
    submitted_raw = latest.get("submitted_at", datetime.datetime.utcnow().isoformat())
    today = submitted_raw[:10].replace("-", "")
    digit_sum = sum(int(c) for c in session_id if c.isdigit())
    suffix = str(1000 + (digit_sum % 9000)).zfill(4)
    dmx_reference = f"DMX-{today}-{suffix}"

    preq = latest.get("prequalification", "N/A")
    preq_icon = _preq_icon(preq)
    status = latest.get("status", "N/A").title()

    try:
        submitted_fmt = datetime.datetime.fromisoformat(
            submitted_raw.replace("Z", "+00:00")
        ).strftime("%B %d, %Y at %H:%M UTC")
    except Exception:
        submitted_fmt = submitted_raw

    dti_val = latest.get("dti_ratio", "N/A")
    ltv_val = latest.get("ltv_ratio", "N/A")
    try:
        dti_display = f"{float(dti_val):.1%}"
    except (ValueError, TypeError):
        dti_display = dti_val
    try:
        ltv_display = f"{float(ltv_val):.1%}"
    except (ValueError, TypeError):
        ltv_display = ltv_val

    return (
        f"## 🏠 MORTGAGE APPLICATION STATUS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"### 🔖 DMX Reference: `{dmx_reference}`\n\n"
        f"| Field | Value |\n"
        "|---|---|\n"
        f"| **Borrower** | {latest.get('borrower_name', 'N/A')} |\n"
        f"| **Status** | 🔵 {status} |\n"
        f"| **Pre-Qualification** | {preq_icon} {preq} |\n"
        f"| **Submitted** | {submitted_fmt} |\n"
        "\n---\n\n"
        "### 📋 Application Details\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Property Address** | {latest.get('property_address', 'N/A')} |\n"
        f"| **Property Type** | {latest.get('property_type', 'N/A')} |\n"
        f"| **Loan Purpose** | {latest.get('loan_purpose', 'N/A')} |\n"
        f"| **Purchase Price** | {latest.get('purchase_price', 'N/A')} |\n"
        f"| **Loan Amount** | {latest.get('loan_amount', 'N/A')} |\n"
        f"| **Employment Status** | {latest.get('employment_status', 'N/A')} |\n"
        f"| **Annual Income** | {latest.get('annual_income', 'N/A')} |\n"
        f"| **Credit Score Range** | {latest.get('credit_score_range', 'N/A')} |\n"
        f"| **DTI Ratio** | {dti_display} |\n"
        f"| **LTV Ratio** | {ltv_display} |\n"
        "\n---\n\n"
        "### ✅ Next Steps\n\n"
        "- A loan officer will be in touch to verify your information and schedule a credit pull.\n"
        "- Have your W-2s, pay stubs, and bank statements ready.\n\n"
        f"💬 **Have questions?** [Chat with our virtual mortgage agent]({_VIRTUAL_AGENT_URL})\n"
    )


@mcp.tool()
def get_virtual_agent_link() -> str:
    """
    Provide the link to the live virtual mortgage agent (avatar chatbot).

    Use this when the user wants to speak with a virtual agent, talk to an
    avatar, chat with a mortgage specialist, or get live assistance, e.g.:
    - "I want to speak with an agent"
    - "can I talk to someone?"
    - "connect me with a virtual agent"
    - "I'd like to chat with a mortgage specialist"
    - "show me the avatar chat"
    - "I prefer to speak with someone"
    - "talk to a human / agent / advisor"

    Do NOT use this for submitting applications → use submit_mortgage_application.
    """
    return (
        "## 💬 VIRTUAL MORTGAGE AGENT\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "You can speak with our virtual mortgage specialist **right now** —\n"
        "voice or text chat available 24 / 7.\n\n"
        f"### [→ Start a conversation with your mortgage agent]({_VIRTUAL_AGENT_URL})\n\n"
        f"`{_VIRTUAL_AGENT_URL}`\n\n"
        "---\n\n"
        "The virtual agent can help you with:\n\n"
        "- Answering questions about your application\n"
        "- Explaining loan types, rates, and eligibility\n"
        "- Walking through the mortgage process step by step\n"
        "- Scheduling a call with a licensed loan officer\n"
    )
