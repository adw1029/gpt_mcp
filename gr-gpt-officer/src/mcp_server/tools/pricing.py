import re
from mcp_server.registry import mcp

_BASE_RATES = {
    ("conventional", 30): 6.875,
    ("conventional", 15): 6.250,
    ("fha", 30): 6.625,
    ("va", 30): 6.375,
    ("usda", 30): 6.500,
    ("jumbo", 30): 7.125,
}

_CREDIT_ADJ = {
    "760+": -0.25,
    "720-759": 0.00,
    "680-719": 0.25,
    "640-679": 0.50,
    "600-639": 0.875,
    "below 600": 1.375,
}

_ELIGIBLE_PRODUCTS = {
    "760+": ["Conventional 30yr", "Conventional 15yr", "Jumbo 30yr", "VA 30yr", "USDA 30yr"],
    "720-759": ["Conventional 30yr", "Conventional 15yr", "Jumbo 30yr", "VA 30yr", "USDA 30yr"],
    "680-719": ["Conventional 30yr", "Conventional 15yr", "FHA 30yr", "VA 30yr", "USDA 30yr"],
    "640-679": ["FHA 30yr", "VA 30yr", "USDA 30yr"],
    "600-639": ["FHA 30yr (10% down required if score < 580)"],
    "below 600": ["Manual underwriting required"],
}

_LENDER_CREDITS = {
    "760+": "Up to 0.5 points ($0.5% of loan) in lender credits available at par pricing",
    "720-759": "Up to 0.25 points in lender credits at par",
    "680-719": "Lender credits available at above-par rate only",
    "640-679": "No lender credits at current pricing tier",
    "600-639": "No lender credits available",
    "below 600": "N/A",
}


def _parse_dollars(value: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except (ValueError, TypeError):
        return 0.0


def _get_adj(credit_score_range: str) -> float:
    key = credit_score_range.strip().lower().replace(" ", "").replace("-", "")
    for k, adj in _CREDIT_ADJ.items():
        norm = k.replace("-", "").replace("+", "").replace(" ", "")
        if norm in key or key in norm:
            return adj
    return 0.25


def _monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    r = annual_rate / 100 / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


@mcp.tool()
def get_loan_pricing_scenario(
    loan_amount: str,
    ltv: str,
    credit_score_range: str,
    loan_type: str,
    points: str = "0",
) -> str:
    """
    Generate a rate sheet and pricing scenario for a loan — for internal LO use only.

    Use this when an LO asks about rates, eligibility, or pricing, e.g.:
    - "What is today's rate for a 30-year fixed conventional loan at 80% LTV?"
    - "Show me all loan products [Name] is eligible for based on their profile."
    - "What is the best rate I can offer with [X] points bought down?"
    - "Is this borrower eligible for an FHA loan given their DTI and credit score?"
    - "Generate a rate comparison for 15-year vs 30-year for loan #[XXXXX]."
    - "What are the current lender credits available on this loan scenario?"
    - "Show me any pricing exceptions or adjustments applied to file #[XXXXX]."

    Parameters:
    - loan_amount: e.g. "$400,000"
    - ltv: e.g. "80" or "80%" (loan-to-value ratio)
    - credit_score_range: "760+", "720-759", "680-719", "640-679", "600-639", or "Below 600"
    - loan_type: "conventional", "fha", "va", "usda", or "jumbo"
    - points: points to buy down rate, e.g. "0", "1", "2" (default: "0")
    """
    amt = _parse_dollars(loan_amount)
    ltv_val = _parse_dollars(ltv.replace("%", ""))
    pts = _parse_dollars(points)
    lt_key = loan_type.strip().lower()

    adj = _get_adj(credit_score_range)
    base = _BASE_RATES.get((lt_key, 30), 6.875)
    rate = round(base + adj - (pts * 0.25), 3)
    apr = round(rate + 0.175, 3)
    monthly = _monthly_payment(amt, rate, 30)
    monthly_15 = _monthly_payment(amt, round(_BASE_RATES.get(("conventional", 15), 6.25) + adj, 3), 15)

    eligible_products = []
    for k, v in _ELIGIBLE_PRODUCTS.items():
        norm_k = k.replace("-", "").replace("+", "").replace(" ", "")
        norm_input = credit_score_range.strip().lower().replace("-", "").replace("+", "").replace(" ", "")
        if norm_k in norm_input or norm_input in norm_k:
            eligible_products = v
            break
    if not eligible_products:
        eligible_products = ["Consult guidelines"]

    lender_credits = "N/A"
    for k, v in _LENDER_CREDITS.items():
        norm_k = k.replace("-", "").replace("+", "").replace(" ", "")
        norm_input = credit_score_range.strip().lower().replace("-", "").replace("+", "").replace(" ", "")
        if norm_k in norm_input or norm_input in norm_k:
            lender_credits = v
            break

    buydown_rows = ""
    for p in [0, 0.5, 1.0, 2.0]:
        bd_rate = round(base + adj - (p * 0.25), 3)
        bd_monthly = _monthly_payment(amt, bd_rate, 30)
        cost = amt * p / 100
        buydown_rows += (
            f"| {p:.1f} pts | ${cost:,.0f} | {bd_rate:.3f}% | ${bd_monthly:,.0f}/mo |\n"
        )

    fha_eligible = ltv_val <= 96.5 and adj <= 0.875
    fha_note = (
        "✅ Eligible for FHA based on LTV and credit profile."
        if fha_eligible else
        "❌ FHA ineligible — check LTV (max 96.5%) and credit score (min 580 for 3.5% down)."
    )

    return (
        f"## 💲 PRICING SCENARIO — INTERNAL\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 📊 Scenario Inputs\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Loan Amount** | ${amt:,.0f} |\n"
        f"| **LTV** | {ltv_val:.1f}% |\n"
        f"| **Credit Score Range** | {credit_score_range} |\n"
        f"| **Loan Type** | {loan_type.title()} |\n"
        f"| **Points** | {pts:.1f} |\n"
        "\n---\n\n"
        "### 📈 Pricing at Par\n\n"
        "| | 30-Year Fixed | 15-Year Fixed |\n"
        "|---|---|---|\n"
        f"| **Rate** | {rate:.3f}% | {round(_BASE_RATES.get(('conventional', 15), 6.25) + adj, 3):.3f}% |\n"
        f"| **APR** | {apr:.3f}% | — |\n"
        f"| **Est. Monthly P&I** | ${monthly:,.0f} | ${monthly_15:,.0f} |\n"
        "\n---\n\n"
        "### 🔽 Buydown Options\n\n"
        "| Points | Cost | Rate | Monthly P&I |\n"
        "|---|---|---|---|\n"
        f"{buydown_rows}"
        "\n---\n\n"
        "### 🏦 Product Eligibility\n\n"
        + "\n".join(f"- {p}" for p in eligible_products) + "\n\n"
        f"**FHA Check:** {fha_note}\n\n"
        "---\n\n"
        f"### 💳 Lender Credits\n\n_{lender_credits}_\n\n"
        "---\n\n"
        "> _As of March 30, 2026. Rates subject to change. For exceptions or adjustments, "
        "use `get_lo_borrower_profile` to check pricing exceptions on file._\n"
    )
