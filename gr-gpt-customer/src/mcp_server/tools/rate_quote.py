import re
from mcp_server.registry import mcp

_BASE_RATES = {
    ("conventional", 30): 6.875,
    ("conventional", 15): 6.250,
    ("fha", 30): 6.625,
    ("fha", 15): 6.000,
    ("va", 30): 6.375,
    ("va", 15): 5.875,
    ("usda", 30): 6.500,
    ("jumbo", 30): 7.125,
    ("jumbo", 15): 6.625,
    ("arm", 5): 6.125,
    ("arm", 7): 6.250,
    ("arm", 10): 6.500,
}

_CREDIT_ADJ = {
    "760+": -0.25,
    "720-759": 0.00,
    "680-719": 0.25,
    "640-679": 0.50,
    "600-639": 0.875,
    "below 600": 1.375,
}

_BUYDOWN = [
    (0, 0.0),
    (0.5, 0.125),
    (1.0, 0.25),
    (2.0, 0.375),
]


def _parse_dollars(value: str) -> float:
    try:
        return float(re.sub(r"[^\d.]", "", str(value)))
    except (ValueError, TypeError):
        return 0.0


def _credit_adj(credit_score_range: str) -> float:
    key = credit_score_range.strip().lower().replace(" ", "")
    for k, adj in _CREDIT_ADJ.items():
        if k.replace("-", "").replace("+", "").replace(" ", "") in key or key in k.replace("-", "").replace("+", "").replace(" ", ""):
            return adj
    return 0.25


def _monthly_payment(principal: float, annual_rate: float, years: int) -> float:
    r = annual_rate / 100 / 12
    n = years * 12
    if r == 0:
        return principal / n
    return principal * r * (1 + r) ** n / ((1 + r) ** n - 1)


@mcp.tool()
def get_rate_quote(
    loan_type: str,
    purchase_price: str,
    down_payment: str,
    credit_score_range: str,
    loan_term_years: int,
) -> str:
    """
    Generate a real-time mortgage rate quote with monthly payment estimate.

    Use this when a borrower asks about rates, payments, or rate comparisons, e.g.:
    - "What are today's mortgage rates?"
    - "What would my monthly payment be on a $400,000 loan?"
    - "How does my credit score affect my interest rate?"
    - "What rate can I lock in for a 30-year fixed?"
    - "How much can I save by buying down the rate with points?"
    - "Compare rates for 15-year vs. 30-year loans"

    Parameters:
    - loan_type: "conventional", "fha", "va", "usda", "jumbo", or "arm"
    - purchase_price: e.g. "$500,000" or "500000"
    - down_payment: e.g. "$100,000" or "20%"
    - credit_score_range: one of "760+", "720-759", "680-719", "640-679", "600-639", "Below 600"
    - loan_term_years: 30, 15, or for ARM: 5, 7, or 10 (represents fixed period)

    Do NOT use this for:
    - Loan product descriptions → use get_loan_products
    - Eligibility determination → use check_borrower_eligibility
    """
    price = _parse_dollars(purchase_price)
    if "%" in str(down_payment):
        pct = _parse_dollars(down_payment) / 100
        dp = price * pct
    else:
        dp = _parse_dollars(down_payment)

    loan_amount = price - dp if price > dp else price
    ltv = (loan_amount / price * 100) if price > 0 else 0
    down_pct = (dp / price * 100) if price > 0 else 0

    lt_key = loan_type.strip().lower()
    if lt_key in ("30yr", "30-year", "fixed", "30 year"):
        lt_key, loan_term_years = "conventional", 30
    elif lt_key in ("15yr", "15-year", "15 year"):
        lt_key, loan_term_years = "conventional", 15

    base = _BASE_RATES.get((lt_key, loan_term_years))
    if base is None:
        closest_term = min(
            [k[1] for k in _BASE_RATES if k[0] == lt_key],
            key=lambda t: abs(t - loan_term_years),
            default=30,
        )
        base = _BASE_RATES.get((lt_key, closest_term), 6.875)
        loan_term_years = closest_term

    adj = _credit_adj(credit_score_range)
    rate = round(base + adj, 3)
    apr = round(rate + 0.175, 3)

    monthly = _monthly_payment(loan_amount, rate, loan_term_years)
    total_paid = monthly * loan_term_years * 12
    total_interest = total_paid - loan_amount

    pmi_monthly = round(loan_amount * 0.0065 / 12) if ltv > 80 and lt_key == "conventional" else 0
    mip_monthly = round(loan_amount * 0.0055 / 12) if lt_key == "fha" else 0
    mortgage_insurance = pmi_monthly or mip_monthly

    buydown_rows = ""
    for pts, reduction in _BUYDOWN:
        bd_rate = round(rate - reduction, 3)
        bd_monthly = _monthly_payment(loan_amount, bd_rate, loan_term_years)
        monthly_savings = monthly - bd_monthly
        cost = loan_amount * pts / 100
        breakeven_months = int(cost / monthly_savings) if monthly_savings > 0 else 0
        buydown_rows += (
            f"| {pts:.1f} pts (${cost:,.0f}) | {bd_rate:.3f}% | "
            f"${bd_monthly:,.0f}/mo | ${monthly_savings:,.0f}/mo savings | "
            f"{'N/A' if breakeven_months == 0 else f'{breakeven_months} mos'} |\n"
        )

    rate_15 = _BASE_RATES.get(("conventional", 15), 6.25) + adj
    monthly_15 = _monthly_payment(loan_amount, rate_15, 15)
    interest_15 = monthly_15 * 180 - loan_amount

    rate_30 = _BASE_RATES.get(("conventional", 30), 6.875) + adj
    monthly_30 = _monthly_payment(loan_amount, rate_30, 30)
    interest_30 = monthly_30 * 360 - loan_amount

    disclaimer = (
        "\n> ⚠️ _Rates shown are estimates based on current market data and are subject to change. "
        "Final rate is determined upon loan approval and lock. As of March 2026._\n"
    )

    return (
        f"## 💰 RATE QUOTE — {loan_type.upper()} {loan_term_years}-YR\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 📊 Loan Summary\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Purchase Price** | ${price:,.0f} |\n"
        f"| **Down Payment** | ${dp:,.0f} ({down_pct:.1f}%) |\n"
        f"| **Loan Amount** | ${loan_amount:,.0f} |\n"
        f"| **LTV** | {ltv:.1f}% |\n"
        f"| **Credit Score Range** | {credit_score_range} |\n"
        "\n---\n\n"
        "### 📈 Your Rate\n\n"
        "| | Value |\n"
        "|---|---|\n"
        f"| **Interest Rate** | **{rate:.3f}%** |\n"
        f"| **APR** | {apr:.3f}% |\n"
        f"| **Est. Monthly P&I** | **${monthly:,.0f}** |\n"
        + (f"| **PMI (LTV > 80%)** | ${pmi_monthly:,.0f}/mo |\n" if pmi_monthly else "")
        + (f"| **MIP (FHA)** | ${mip_monthly:,.0f}/mo |\n" if mip_monthly else "")
        + (f"| **Est. Total Monthly** | **${monthly + mortgage_insurance:,.0f}** |\n" if mortgage_insurance else "")
        + f"| **Total Interest (life of loan)** | ${total_interest:,.0f} |\n"
        "\n---\n\n"
        "### 🔽 Buydown Options (Points)\n\n"
        "| Points Paid | Rate | Monthly P&I | Savings | Break-Even |\n"
        "|---|---|---|---|---|\n"
        f"{buydown_rows}"
        "\n---\n\n"
        "### ⚖️ 15-Year vs. 30-Year Comparison\n\n"
        "| | 15-Year Fixed | 30-Year Fixed |\n"
        "|---|---|---|\n"
        f"| **Rate** | {rate_15:.3f}% | {rate_30:.3f}% |\n"
        f"| **Monthly P&I** | ${monthly_15:,.0f} | ${monthly_30:,.0f} |\n"
        f"| **Total Interest** | ${interest_15:,.0f} | ${interest_30:,.0f} |\n"
        f"| **Interest Savings (15yr)** | **${interest_30 - interest_15:,.0f}** | — |\n"
        f"{disclaimer}"
    )
