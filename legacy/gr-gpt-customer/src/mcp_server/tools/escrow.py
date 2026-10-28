from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_escrow_and_insurance(loan_id: str) -> str:
    """
    Return escrow breakdown, PMI details, homeowners insurance status, and flood insurance requirement.

    Use this when a borrower asks about escrow, PMI, or insurance, e.g.:
    - "Will I be required to pay PMI on my loan?"
    - "What is my estimated escrow payment each month?"
    - "Has my homeowners insurance been verified and accepted?"
    - "Has my property tax estimate been added to my escrow account?"
    - "Is flood insurance required on my property?"
    - "When does PMI get removed from my loan?"

    Do NOT use this for:
    - Closing cash amounts → use get_closing_status
    - Rate lock details → use get_rate_lock_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`. Please check your loan ID."
        )

    esc = item.get("escrow", {})
    if not esc:
        return (
            f"## 🏦 Escrow & Insurance — #{loan_id}\n\n"
            "Escrow details are not yet calculated. They will be available once your appraisal "
            "and insurance are verified.\n\n"
            "Use `get_loan_status` to check your current stage."
        )

    pmi_req = esc.get("pmi_required", False)
    pmi_monthly = esc.get("pmi_monthly", 0)
    pmi_ltv = esc.get("pmi_removal_ltv", "78")
    pmi_years = esc.get("pmi_years_estimate", "—")
    monthly_escrow = esc.get("monthly_escrow", 0)
    tax_monthly = esc.get("property_tax_monthly", 0)
    hoi_monthly = esc.get("hoi_monthly", 0)
    hoi_verified = esc.get("hoi_verified", False)
    hoi_carrier = esc.get("hoi_carrier", "—")
    flood_req = esc.get("flood_insurance_required", False)

    pmi_section = ""
    if pmi_req:
        pmi_section = (
            "\n### 🛡️ PMI (Private Mortgage Insurance)\n\n"
            f"**PMI is required** because your LTV is above 80%.\n\n"
            "| Field | Value |\n"
            "|---|---|\n"
            f"| **Monthly PMI** | ${float(pmi_monthly):,.0f}/mo |\n"
            f"| **PMI Removal LTV** | {pmi_ltv}% |\n"
            f"| **Estimated PMI Duration** | ~{pmi_years} years |\n\n"
            f"> 💡 PMI is automatically removed when your loan balance reaches **{pmi_ltv}% LTV** "
            "(based on original amortization schedule). You can also request removal earlier by "
            "demonstrating your equity through a new appraisal once you reach 80% LTV.\n"
        )
    else:
        pmi_section = (
            "\n### 🛡️ PMI\n\n✅ **PMI is not required** for your loan (LTV ≤ 80% or VA/USDA loan).\n"
        )

    flood_section = ""
    if flood_req:
        flood_section = (
            "\n### 🌊 Flood Insurance\n\n"
            "⚠️ **Flood insurance IS required** for your property.\n\n"
            "Your property is located in a FEMA Special Flood Hazard Area. "
            "You must obtain and maintain flood insurance as a condition of your loan. "
            "Contact your homeowners insurance carrier or visit FloodSmart.gov.\n"
        )
    else:
        flood_section = (
            "\n### 🌊 Flood Insurance\n\n"
            "✅ **Flood insurance is NOT required** for your property.\n\n"
            "Your property is in FEMA Zone X — standard flood insurance is not mandatory, "
            "though you may purchase it optionally.\n"
        )

    return (
        f"## 🏦 ESCROW & INSURANCE — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "### 📊 Monthly Escrow Breakdown\n\n"
        "| Component | Monthly Amount |\n"
        "|---|---|\n"
        f"| **Property Tax** | ${float(tax_monthly):,.0f}/mo |\n"
        f"| **Homeowners Insurance (HOI)** | ${float(hoi_monthly):,.0f}/mo |\n"
        + (f"| **PMI** | ${float(pmi_monthly):,.0f}/mo |\n" if pmi_req else "")
        + f"| **Total Escrow** | **${float(monthly_escrow):,.0f}/mo** |\n"
        "\n---\n\n"
        "### 🏠 Homeowners Insurance\n\n"
        "| Field | Status |\n"
        "|---|---|\n"
        f"| **Status** | {'✅ Verified and accepted' if hoi_verified else '⏳ Pending verification'} |\n"
        f"| **Carrier** | {hoi_carrier} |\n\n"
        + ("" if hoi_verified else
            "> ⚠️ **Action required:** Upload your homeowners insurance declaration page "
            "to your document portal. HOI must be verified before closing.\n")
        + f"{pmi_section}"
        + f"{flood_section}"
    )
