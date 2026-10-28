import re
from mcp_server.registry import mcp

_CREDIT_PRODUCTS = {
    "760+": ["Conventional", "VA", "USDA", "Jumbo"],
    "720-759": ["Conventional", "VA", "USDA", "Jumbo"],
    "680-719": ["Conventional", "FHA", "VA", "USDA"],
    "640-679": ["FHA", "VA", "USDA"],
    "600-639": ["FHA (10% down if < 580)"],
    "below 600": ["Manual underwriting required — consult a loan officer"],
}

_DOC_CHECKLIST = [
    "✅ Government-issued photo ID",
    "✅ Most recent 30-day pay stubs (all jobs)",
    "✅ Last 2 years W-2s or 1099s",
    "✅ Last 2 years federal tax returns (self-employed: include business returns)",
    "✅ Last 2 months bank/asset statements (all accounts)",
    "✅ Signed purchase contract (for purchase loans)",
    "✅ Homeowners insurance quote",
    "✅ Mortgage statements for any existing properties",
]


def _parse_dollars(value: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except (ValueError, TypeError):
        return 0.0


def _dti_assessment(dti: float) -> tuple[str, str]:
    if dti < 0.36:
        return "Excellent ✅", "Well within standard guidelines — strong approval signal."
    elif dti < 0.43:
        return "Acceptable ✅", "Within conventional guidelines. Some lenders prefer < 43%."
    elif dti < 0.50:
        return "Elevated ⚠️", "Above 43% — FHA or manual underwriting may be required."
    else:
        return "High ❌", "Exceeds standard limits. Debt reduction or a co-borrower is recommended."


def _ltv_assessment(ltv: float) -> tuple[str, str]:
    if ltv <= 0.80:
        return "Strong ✅", "LTV ≤ 80% — no PMI required on conventional."
    elif ltv <= 0.965:
        return "Standard ✅", "FHA (3.5% min) or conventional with PMI."
    else:
        return "Requires Review ⚠️", "LTV > 96.5% exceeds FHA maximum. Down payment assistance may help."


@mcp.tool()
def check_borrower_eligibility(
    annual_income: str,
    monthly_debts: str,
    purchase_price: str,
    down_payment: str,
    credit_score_range: str,
    employment_type: str,
) -> str:
    """
    Run a soft eligibility and affordability check for a prospective borrower.
    No credit pull required — this is an estimate only.

    Use this when a borrower asks about eligibility, affordability, or pre-qualification, e.g.:
    - "How much can I afford to borrow?"
    - "What credit score do I need to qualify?"
    - "What is the minimum down payment required?"
    - "Can a co-borrower help me qualify for a larger loan?"
    - "I'm self-employed — can I still get a mortgage?"
    - "Does my student loan debt affect my borrowing capacity?"
    - "Can I get pre-qualified without a hard credit pull?"
    - "What documents do I need to apply?"

    Parameters:
    - annual_income: gross annual income before taxes, e.g. "$95,000"
    - monthly_debts: existing monthly debt payments (car, student loans, credit cards) — NOT including new mortgage, e.g. "$850"
    - purchase_price: target home purchase price, e.g. "$420,000"
    - down_payment: amount or percentage, e.g. "$42,000" or "10%"
    - credit_score_range: "760+", "720-759", "680-719", "640-679", "600-639", or "Below 600"
    - employment_type: "W-2 Employee", "Self-employed", "Retired", or "Other"

    Do NOT use this for:
    - Product descriptions → use get_loan_products
    - Rate quotes → use get_rate_quote
    - Existing loan status → use get_loan_status
    """
    income = _parse_dollars(annual_income)
    monthly_income = income / 12 if income > 0 else 1
    existing_debts = _parse_dollars(monthly_debts)
    price = _parse_dollars(purchase_price)

    if "%" in str(down_payment):
        pct = _parse_dollars(down_payment) / 100
        dp = price * pct
    else:
        dp = _parse_dollars(down_payment)

    loan_amount = price - dp if price > dp else price
    ltv = loan_amount / price if price > 0 else 0
    down_pct = (dp / price * 100) if price > 0 else 0

    est_rate = 6.875
    est_payment = loan_amount * (est_rate / 100 / 12) * (1 + est_rate / 100 / 12) ** 360 / ((1 + est_rate / 100 / 12) ** 360 - 1)
    est_escrow = price * 0.012 / 12
    total_monthly = existing_debts + est_payment + est_escrow
    dti = total_monthly / monthly_income if monthly_income > 0 else 1

    max_affordable_payment = monthly_income * 0.43 - existing_debts - est_escrow
    max_loan = max(0, max_affordable_payment / (est_rate / 100 / 12) * (1 - (1 + est_rate / 100 / 12) ** -360))

    dti_label, dti_detail = _dti_assessment(dti)
    ltv_label, ltv_detail = _ltv_assessment(ltv)

    credit_key = credit_score_range.strip().lower().replace(" ", "")
    eligible_products = []
    for k, v in _CREDIT_PRODUCTS.items():
        if k.replace("-", "").replace("+", "") in credit_key or credit_key in k.replace("-", "").replace("+", ""):
            eligible_products = v
            break
    if not eligible_products:
        eligible_products = ["Consult a loan officer for product options"]

    if dti < 0.43 and ltv <= 0.97 and any(s in credit_score_range for s in ["760", "720", "680"]):
        preq = "LIKELY ELIGIBLE ✅"
        preq_note = "Based on the information provided, this scenario meets standard eligibility guidelines."
    elif dti < 0.50 and ltv <= 0.965:
        preq = "CONDITIONAL ⚠️"
        preq_note = "May qualify with documentation, compensating factors, or a co-borrower."
    else:
        preq = "NEEDS REVIEW 🔍"
        preq_note = "One or more factors are outside standard guidelines. A loan officer review is recommended."

    self_emp_note = (
        "\n> 💼 **Self-Employed Tip:** Rate requires 2 years of self-employment history with tax returns "
        "(personal + business). Lenders use the average net income from Schedule C/K-1, not gross revenue. "
        "A CPA letter confirming business stability is highly recommended.\n"
        if "self" in employment_type.lower() else ""
    )

    coborrower_note = (
        "\n### 👥 Can a Co-Borrower Help?\n\n"
        "Yes — adding a co-borrower (e.g. spouse, partner, or family member) combines both incomes, "
        f"which can raise your max loan from **~${max_loan:,.0f}** to a higher amount. "
        "The co-borrower's debts are also included in the DTI calculation.\n"
    )

    doc_list = "\n".join(_DOC_CHECKLIST)

    return (
        f"## 📋 ELIGIBILITY ESTIMATE\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"**Pre-Qualification Signal: {preq}**  \n_{preq_note}_\n\n"
        "---\n\n"
        "### 📊 Your Numbers\n\n"
        "| Metric | Value | Assessment |\n"
        "|---|---|---|\n"
        f"| **Purchase Price** | ${price:,.0f} | — |\n"
        f"| **Down Payment** | ${dp:,.0f} ({down_pct:.1f}%) | — |\n"
        f"| **Loan Amount** | ${loan_amount:,.0f} | — |\n"
        f"| **LTV Ratio** | {ltv:.1%} | {ltv_label} — {ltv_detail} |\n"
        f"| **DTI Ratio** | {dti:.1%} | {dti_label} — {dti_detail} |\n"
        f"| **Est. Monthly P&I** | ${est_payment:,.0f} | At ~6.875% 30-yr fixed |\n"
        f"| **Max Affordable Loan** | ~${max_loan:,.0f} | At 43% DTI limit |\n"
        "\n---\n\n"
        "### 🏦 Eligible Loan Products\n\n"
        + "\n".join(f"- **{p}**" for p in eligible_products) + "\n"
        f"{self_emp_note}"
        f"{coborrower_note}"
        "\n---\n\n"
        "### 📁 Documents You'll Need\n\n"
        f"{doc_list}\n\n"
        "---\n\n"
        "> ⚠️ _This is a soft estimate — no credit pull required. Final eligibility is determined "
        "by a licensed underwriter after a full application with hard credit pull._\n\n"
        "**Ready to apply?** Use `get_application_guide()` for next steps.\n"
    )
