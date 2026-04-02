from mcp_server.registry import mcp
from mcp_server.utils.portal import lookup_borrower_portal


@mcp.tool()
def get_rate_lock_status(loan_id: str) -> str:
    """
    Return the rate lock status — locked rate, APR, expiry, extension options, and float-down eligibility.

    Use this when a borrower asks about their rate lock, e.g.:
    - "When does my rate lock expire?"
    - "Can I extend my rate lock and what does it cost?"
    - "Has my rate lock been confirmed?"
    - "Can I switch loan programs after I have applied?"
    - "What is my current interest rate and APR?"
    - "Can I request a float-down if rates have dropped?"
    - "Is my rate locked? What rate did I lock at?"
    - "What is my current APR, not just the interest rate?"
    - "Are there float-down options available since rates dropped?"
    - "Has my rate lock extension been confirmed?"

    Do NOT use this for:
    - Closing details → use get_closing_status
    - Overall loan status → use get_loan_status
    """
    item = lookup_borrower_portal(loan_id)
    if not item:
        return (
            f"## ❌ Loan Not Found\n\n"
            f"No record found for loan `{loan_id}`. Please check your loan ID."
        )

    rl = item.get("rate_lock", {})
    if not rl or not rl.get("confirmed"):
        not_locked_msg = (
            "Your rate has **not yet been locked**. "
            "You are currently floating at market — this means your rate may change until you lock.\n\n"
            "**To lock your rate**, contact your loan officer. Once locked, your rate is protected "
            "for the lock period regardless of market movement.\n\n"
            "Use `get_loan_officer_contact` to reach your loan officer."
        )
        if rl and not rl.get("confirmed"):
            return (
                f"## 🔓 RATE LOCK STATUS — #{loan_id}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{not_locked_msg}\n"
            )
        return (
            f"## 🔓 RATE LOCK STATUS — #{loan_id}\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"{not_locked_msg}\n"
        )

    rate = rl.get("rate", "—")
    apr = rl.get("apr", "—")
    lock_date = rl.get("lock_date", "—")
    expiry = rl.get("expiry_date", "—")
    days_remaining = int(rl.get("days_remaining", 0))
    ext_pts = rl.get("extension_cost_points", "—")
    ext_dollars = rl.get("extension_cost_dollars", "—")
    float_down = rl.get("float_down_available", False)
    float_rate = rl.get("float_down_rate")
    switch_eligible = rl.get("program_switch_eligible", False)

    urgency = ""
    if days_remaining <= 5:
        urgency = (
            f"\n> 🚨 **URGENT — Rate lock expires in {days_remaining} day(s)!** "
            "Contact your loan officer immediately to discuss extension options.\n"
        )
    elif days_remaining <= 10:
        urgency = (
            f"\n> ⚠️ **Rate lock expires in {days_remaining} days.** "
            "Monitor your closing timeline closely.\n"
        )

    ext_section = (
        "\n### 🔁 Extension Options\n\n"
        "| Extension Period | Cost |\n"
        "|---|---|\n"
        f"| **15-day extension** | {ext_pts} points (~${ext_dollars}) |\n"
        "| **30-day extension** | Ask your loan officer for current pricing |\n\n"
        "_Extension must be requested before the lock expiry date._\n"
    )

    float_section = ""
    if float_down:
        float_section = (
            "\n### 📉 Float-Down Option Available\n\n"
            f"Current market rates have dropped. You may be eligible for a float-down.\n\n"
            + (f"**New rate available:** {float_rate}%\n\n" if float_rate else "")
            + "**To request a float-down**, contact your loan officer today — "
            "this option is time-sensitive and must be exercised before your closing date.\n"
        )
    else:
        float_section = (
            "\n### 📉 Float-Down\n\n"
            "_Float-down is not currently available for your rate lock. "
            "This option becomes available if market rates drop significantly below your locked rate._\n"
        )

    switch_section = (
        "\n### 🔄 Loan Program Switch\n\n"
        + (
            "You **may be eligible** to switch loan programs (e.g. from Conventional to FHA). "
            "Contact your loan officer — a program switch will require a new rate lock and may reset timelines.\n"
            if switch_eligible else
            "A loan program switch is **not available** at this stage of your loan.\n"
        )
    )

    return (
        f"## 🔒 RATE LOCK STATUS — #{loan_id}\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"{urgency}"
        "### 📈 Your Locked Rate\n\n"
        "| Field | Value |\n"
        "|---|---|\n"
        f"| **Status** | ✅ Confirmed & Locked |\n"
        f"| **Interest Rate** | **{rate}%** |\n"
        f"| **APR** | {apr}% _(inclusive of points and fees)_ |\n"
        f"| **Lock Date** | {lock_date} |\n"
        f"| **Lock Expiry** | {expiry} |\n"
        f"| **Days Remaining** | {'⚠️ ' if days_remaining <= 10 else ''}{days_remaining} days |\n"
        f"{ext_section}"
        f"{float_section}"
        f"{switch_section}"
    )
