from mcp_server.registry import mcp

_PRODUCTS = {
    "conventional": {
        "name": "Conventional Loan",
        "description": "The most common mortgage type — not government-backed, sold to Fannie Mae or Freddie Mac.",
        "down_payment_min": "3% (with PMI) or 20% (no PMI required)",
        "credit_score_min": "620 (660+ recommended for best pricing)",
        "loan_limit_2026": "$806,500 (conforming); above this is Jumbo",
        "pmi": "Required when LTV > 80%. Automatically removed at 78% LTV.",
        "best_for": "Borrowers with good credit (680+), stable W-2 income, and 5–20% down payment.",
    },
    "fha": {
        "name": "FHA Loan (Federal Housing Administration)",
        "description": "Government-backed loan insured by FHA. More flexible credit and income requirements.",
        "down_payment_min": "3.5% (credit 580+) or 10% (credit 500–579)",
        "credit_score_min": "580 for 3.5% down; 500 for 10% down",
        "loan_limit_2026": "$498,257 (standard); higher in high-cost areas",
        "pmi": "MIP (Mortgage Insurance Premium) required for the life of the loan if < 10% down.",
        "best_for": "First-time buyers, lower credit scores (580–679), or limited down payment savings.",
    },
    "va": {
        "name": "VA Loan (Department of Veterans Affairs)",
        "description": "Zero down payment loan for eligible veterans, active-duty service members, and surviving spouses.",
        "down_payment_min": "0% — no down payment required",
        "credit_score_min": "620 (Rate's minimum; VA has no official minimum)",
        "loan_limit_2026": "No conforming loan limit for eligible full-entitlement borrowers",
        "pmi": "No PMI. Funding fee applies (0.5%–3.3% of loan amount; waived for disabled veterans).",
        "eligibility": "90 days active duty (wartime), 181 days (peacetime), 6 years National Guard/Reserves, or surviving spouse.",
        "best_for": "Eligible veterans and service members — the most favorable terms available.",
    },
    "usda": {
        "name": "USDA Loan (U.S. Dept. of Agriculture)",
        "description": "Zero down payment loan for properties in eligible rural and suburban areas.",
        "down_payment_min": "0% — no down payment required",
        "credit_score_min": "640 (Rate's minimum)",
        "loan_limit_2026": "No set limit; must meet USDA income limits (typically ≤ 115% of area median income)",
        "pmi": "Guarantee fee (1% upfront + 0.35% annual) instead of PMI.",
        "eligibility": "Property must be in a USDA-eligible area (check eligibility map). Income limits apply.",
        "best_for": "Low-to-moderate income buyers purchasing in eligible rural/suburban areas.",
    },
    "jumbo": {
        "name": "Jumbo Loan",
        "description": "Conventional loan exceeding the conforming loan limit — not eligible for sale to Fannie/Freddie.",
        "down_payment_min": "10–20% (varies by lender and loan size)",
        "credit_score_min": "700+ (720+ recommended)",
        "loan_limit_2026": "Above $806,500 (conforming limit)",
        "pmi": "Typically not required with 20% down. Lender-specific rules above that.",
        "best_for": "High-value property purchases in markets like CA, NY, WA. Requires strong financials.",
    },
    "arm": {
        "name": "Adjustable-Rate Mortgage (ARM)",
        "description": "Rate is fixed for an initial period (5, 7, or 10 years), then adjusts annually based on market index.",
        "common_terms": "5/1 ARM, 7/1 ARM, 10/1 ARM (fixed period / adjustment frequency)",
        "initial_rate": "Typically 0.5–1.25% lower than a 30-year fixed at time of origination",
        "rate_caps": "Typically 2% per adjustment, 5–6% lifetime cap above initial rate",
        "best_for": "Buyers who plan to sell or refinance within the fixed period. Not ideal for long-term holds.",
        "risk": "Monthly payment increases if rates rise after the fixed period.",
    },
}

_ALL_CATALOG = """
| Product | Down Payment Min | Credit Min | Best For |
|---|---|---|---|
| **Conventional** | 3% (PMI) / 20% (no PMI) | 620 | Good credit, stable W-2 income |
| **FHA** | 3.5% | 580 | First-time buyers, lower credit scores |
| **VA** | 0% | 620 | Eligible veterans & service members |
| **USDA** | 0% | 640 | Rural/suburban areas, income limits apply |
| **Jumbo** | 10–20% | 700+ | Loan > $806,500 (high-value properties) |
| **ARM** | 3–20% | 620 | Short-term owners, rate drops anticipated |
"""


@mcp.tool()
def get_loan_products(loan_type: str) -> str:
    """
    Return information about mortgage loan products offered by Rate.

    Use this for any question about loan types, product options, eligibility,
    or product comparisons, e.g.:
    - "What types of home loans does Rate offer?"
    - "What is the difference between a fixed-rate and adjustable-rate mortgage?"
    - "Am I eligible for an FHA loan?"
    - "What is a jumbo loan?"
    - "Can I get a VA loan?"
    - "What is a USDA loan?"
    - "Is a 15-year or 30-year mortgage better for me?"
    - "Tell me about conventional loans"

    Pass loan_type as one of: "all", "conventional", "fha", "va", "usda", "jumbo", "arm".
    Pass "all" (or "overview") to return the full product catalog.

    Do NOT use this for:
    - Rate quotes → use get_rate_quote
    - Eligibility calculations → use check_borrower_eligibility
    - Application guidance → use get_application_guide
    """
    key = loan_type.strip().lower()

    if key in ("all", "overview", "catalog", ""):
        return (
            "## 🏦 RATE MORTGAGE PRODUCT CATALOG\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "_As of March 2026. All products subject to credit approval and underwriting._\n\n"
            f"{_ALL_CATALOG}\n"
            "---\n\n"
            "### 📋 Quick Guidance\n\n"
            "- **Good credit (680+), stable job, 5–20% down?** → Conventional\n"
            "- **First-time buyer or lower credit score?** → FHA\n"
            "- **Veteran or active-duty service member?** → VA (best deal available)\n"
            "- **Buying in a rural/suburban area with limited savings?** → USDA\n"
            "- **Purchase price above $806,500?** → Jumbo\n"
            "- **Planning to sell or refi within 5–7 years?** → ARM (lower initial rate)\n\n"
            "### 📐 15-Year vs. 30-Year Fixed\n\n"
            "| | 30-Year Fixed | 15-Year Fixed |\n"
            "|---|---|---|\n"
            "| **Monthly payment** | Lower | Higher (~40–50% more) |\n"
            "| **Total interest paid** | Higher | Much lower |\n"
            "| **Rate** | Higher | Lower (typically 0.5–0.75% less) |\n"
            "| **Best for** | Cash flow flexibility | Faster equity, lower cost |\n\n"
            "_Type a specific product name (e.g. 'fha' or 'va') for full details._\n"
        )

    product = _PRODUCTS.get(key)
    if not product:
        normalized = {
            "fixed": "conventional", "30yr": "conventional", "15yr": "conventional",
            "government": "fha", "rural": "usda", "veteran": "va", "variable": "arm",
        }
        product = _PRODUCTS.get(normalized.get(key, ""))

    if not product:
        return (
            f"## ❓ Product Not Recognized\n\n"
            f"No product found matching `{loan_type}`.\n\n"
            "Available types: **conventional**, **fha**, **va**, **usda**, **jumbo**, **arm**.\n\n"
            "Try: `get_loan_products(loan_type='all')` for the full catalog."
        )

    name = product["name"]
    lines = [
        f"## 🏠 {name.upper()}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"_{product['description']}_\n\n"
        "| Detail | Value |\n"
        "|---|---|\n"
        f"| **Minimum Down Payment** | {product['down_payment_min']} |\n"
        f"| **Minimum Credit Score** | {product['credit_score_min']} |\n"
    ]
    if "loan_limit_2026" in product:
        lines.append(f"| **2026 Loan Limit** | {product['loan_limit_2026']} |\n")
    if "pmi" in product:
        lines.append(f"| **PMI / MIP** | {product['pmi']} |\n")
    if "eligibility" in product:
        lines.append(f"| **Eligibility** | {product['eligibility']} |\n")
    if "initial_rate" in product:
        lines.append(f"| **Initial Rate Advantage** | {product['initial_rate']} |\n")
    if "rate_caps" in product:
        lines.append(f"| **Rate Caps** | {product['rate_caps']} |\n")

    lines.append(f"\n**Best for:** {product['best_for']}\n")

    if key == "arm":
        lines.append(
            "\n> ⚠️ **ARM Risk:** Monthly payments will increase if market rates rise "
            "after the fixed period. Only recommended if you plan to sell or refinance "
            "before the adjustment begins.\n"
        )

    lines.append(
        "\n---\n\n"
        "_Rates shown are estimates. Final terms determined upon application and credit approval._\n"
    )

    return "".join(lines)
