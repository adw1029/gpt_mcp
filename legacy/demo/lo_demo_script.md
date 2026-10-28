# Loan Officer GPT — Demo Script
**Audience:** Executive / President  
**Persona:** Andrew Cui — loan officer, starting his workday  
**Duration:** ~3 minutes  
**GPT:** `gr-gpt-officer` — `https://pwkcxyo802.execute-api.us-east-2.amazonaws.com/mcp`

---

## System Prompt
```
You are Rate's internal AI assistant for loan officers — precise, efficient, and data-driven.
Help loan officers manage their pipeline, review borrower files, run pricing, and track compliance.

Demo loan officer: Andrew Cui · LO ID: andrew-cui
Auto-use lo_name "Andrew Cui" for any question about "my pipeline", "my loans", "my volume", "my numbers".

CRITICAL TOOL RULES — follow every time:
- ALWAYS call the appropriate tool. Never estimate, summarize, or answer from memory.
- Pipeline questions → call get_lo_pipeline immediately.
- Closing/funding questions for a specific loan → call get_closing_and_funding_status with the loan ID.
- Borrower profile / conditions questions → call get_lo_borrower_profile with the loan ID.
- Compliance questions (CD, LE, TRID) → call get_loan_compliance_status with the loan ID.
- Pricing / rate quote for a new scenario → call get_loan_pricing_scenario.
- Production metrics / analytics → call get_lo_performance_analytics.
- Lead with the most urgent information. Flag expiring locks, open conditions, and compliance risks proactively.
```

---

## Opening — Set the Stage (presenter reads aloud)

> A loan officer manages 20–30 active loans at any given time.
> Every morning, the same problem: five systems to check, a dozen emails,
> and a phone that's already ringing.
>
> What's closing this week? Who has open conditions?
> Has the Closing Disclosure gone out? What's my production looking like?
>
> Before this, getting that picture took 30–45 minutes of system-hopping.
> Watch Andrew Cui get it in under 3 minutes — without logging into anything.

---

## Scene 1 — Pipeline & Borrower Review (~75 sec)

*Andrew opens his laptop. First question is always the same.*

**[PROMPT 1]** *(Pipeline Management)*
> **"Good morning. Give me a full view of my pipeline — what needs my attention today?"**

✅ Tool: `get_lo_pipeline("Andrew Cui")`

> **What's happening:**
> Rate's LOS queried live. All 5 active loans returned, triaged by urgency:
> ⏳ Angela Kim — CTC, lock expires in 6 days, closing Apr 4 → most time-sensitive
> 🚨 Kowalski — CD not sent, 2 conditions open, closing Apr 11 → needs active management today
> 📋 Jamie Torres — 3 conditions in UW, closing Apr 18 → not urgent yet, but can slip
> ⚠️ Ryan Chen — not locked, closing May 10 → floating, strategic follow-up
> ✅ Derek Nguyen — funded Mar 25 → effectively done, stale lock alert (low risk)
>
> **Talking point:**
> *"Andrew just got his morning briefing without opening Encompass or his email.
> The AI triaged his entire pipeline and told him exactly where to focus — in 5 seconds."*

---

**[PROMPT 2]** *(Borrower Profile & Conditions)*
> **"Pull up the full file on Jamie Torres — what conditions are still open and where does the underwriting stand?"**

✅ Tool: `get_lo_borrower_profile("501234002")`

> **What's happening:**
> Complete borrower snapshot: credit 703, W-2 + VOE fully verified, income not an issue.
> 2 hard conditions blocking approval — updated December bank statement (asset validation)
> and gift letter from parents (sourcing). These are the only things standing between
> this file and conditional approval. Closing Apr 18, ~19 days out — still manageable
> but Andrew needs to move on both items today to avoid compressing the CD timeline.
>
> **Talking point:**
> *"The AI didn't just list conditions — it told Andrew which ones are hard stops,
> why each one matters, and what to do first. That's the brief a processor
> would take 10 minutes to write."*

---

## Scene 2 — Compliance & Risk (~45 sec)

*Before Andrew starts his calls, he wants to make sure nothing is heading toward a violation.*

**[PROMPT 3]** *(Compliance — clean file)*
> **"Angela Kim is closing April 4. Has her Closing Disclosure been sent and is the 3-day TRID window still good?"**

✅ Tool: `get_loan_compliance_status("501234004")`

> **What's happening:**
> Rate's compliance audit trail: CD sent Mar 28, acknowledged Mar 28 at 3:47 PM.
> TRID 3-day window: satisfied — April 4 closing is fully supported. No compliance flags on RESPA, HMDA, or Fair Lending.
> Main remaining risk on this file is the lock expiring Apr 5, one day after closing — not a compliance issue, but worth watching.

---

**[PROMPT 4]** *(Compliance — risk alert)*
> **"What about James Kowalski — closing April 11. Has his CD gone out yet?"**

✅ Tool: `get_loan_compliance_status("501234003")`

> **What's happening:**
> LE sent Mar 13 ✅. CD not yet sent — TRID window still OK for now.
> Stage: Conditional Approval. Closing Apr 11 — still manageable, but an active timing watch item.
> Combined with 2 open conditions from Prompt 1, this file has both a disclosure gap
> and conditions to clear inside a 2-week window. Andrew knows exactly what needs to move.
>
> **Talking point:**
> *"Two messages. Andrew now knows which file is clean and which one needs to move today.
> Without the AI, that same check would be two separate LOS lookups and a manual date calculation."*

---

## Scene 3 — Live Pricing & Analytics (~60 sec)

*A new lead just called in. Andrew needs a rate on the spot.*

**[PROMPT 5]** *(Live Pricing Scenario)*
> **"New borrower on the phone — $450,000 purchase, 10% down, credit around 720. What's Rate's pricing today on a 30-year conventional, and what does buying down 1 point get them?"**

✅ Tool: `get_loan_pricing_scenario` × 2 — base rate then buydown

> **What's happening:**
> Rate's pricing engine returns live scenarios side by side:
> - Par (0 pts): 7.125% / APR ~7.30%, monthly P&I $2,729
> - 1-point buydown ($4,050): 6.875%, monthly P&I $2,661 — saves ~$68/mo
> - Break-even: ~60 months (5 years) — the AI frames it as "if they stay >5 years, it makes sense"
> - Note: 90% LTV → PMI applies on top of these numbers
> Andrew walks away with a clean quote script he can read directly to the borrower on the call.
>
> **Talking point:**
> *"A live rate quote with buydown math — while the borrower is on the line.
> No spreadsheet. No pricing engine login. No putting them on hold."*

---

**[PROMPT 6]** *(Performance Analytics)*
> **"Before my afternoon calls — how is my production looking this month versus last?"**

✅ Tool: `get_lo_performance_analytics("Andrew Cui")`

> **What's happening:**
> Andrew's live dashboard: $3.215M this month vs $2.780M last (+15.6%, +2 loans).
> Pull-through 76.8%, avg close time 36 days, leads→apps 4 of 5 (80%) this week.
> Top referral: Keller Williams Chicago North / Agent Dan Park — $4.65M across 9 loans YTD.
> Product mix: 70% Conventional 30yr. 1 refi-eligible borrower in pipeline.
>
> **Talking point:**
> *"Monthly production numbers — without opening a single report.
> Volume, conversion rate, referral sources — all in one message."*

---

## Scene 4 — Document Upload & Auto-Approval (~45 sec)

> ⚠️ **Switch GPT for this scene** — uses `gpt-simple-demo`  
> **Endpoint:** `https://prajna-demo.execute-api.us-east-2.amazonaws.com/mcp`  
> **Loan:** `123456789` — AZ purchase, clean title profile

*A title document just came in for a loan pending upload. Andrew wants to get it into the system and run an instant approval check — without leaving the chat.*

**[PROMPT 7]** *(Document Upload — get secure link)*
> **"I need to upload a title document for loan 123456789 — give me a secure upload link."**

✅ Tool: `get_upload_url("123456789")`

> **What's happening:**
> The AI generates a secure presigned upload link to Rate's S3 document store.
> Andrew gets a one-click URL — drag, drop, done. No VPN, no shared drive, no email attachment.
> Link expires in 5 minutes — the AI reminds him to open it now and offers to regenerate if it expires.
>
> *→ Presenter: click the link, upload any PDF to simulate the upload, then say the next prompt.*

---

**[PROMPT 8a]** *(Auto-Approval check)*
> **"I've uploaded the title doc for loan 123456789 — run the auto-approval check on it."**

✅ Tool: `check_loan_approval("123456789", "title")`

> **What's happening:**
> The approval engine fires instantly — 10+ underwriting rules evaluated:
> LTV ~77%, AZ (low-risk state), clean purchase, verified seller + parcel on file, title doc confirmed uploaded.
> Score: **95/105 — APPROVED.** Rule-by-rule breakdown shown.
> Minor flag: HOA detected — routine covenant follow-up, not a blocker.

---

**[PROMPT 8b]** *(Portal link)*
> **"And if I need a deeper review, how do I get to the auto-approval portal?"**

> ⚠️ **Say "auto-approval portal"** exactly — not "portal" or "dashboard". The GPT has a separate virtual agent tool and will route to `avatar.prajnagpt.net` if the wording is vague.

✅ Tool: `get_auto_approval_portal`

> **What's happening:**
> Direct link returned: `https://autoapproval.prajnagpt.net/login`
> AI explains: open the loan inside the portal, move from quick check to the full title review workflow for lien checks, title chain, and final validation.
>
> **Talking point:**
> *"Upload, instant rule engine, scored verdict, portal handoff — four steps, three messages.
> The LO never left the conversation."*

---

## The Close (presenter reads aloud)

> Andrew started his morning not knowing where his pipeline stood.
> Eight prompts later he had reviewed his full pipeline, dug into a borrower file,
> cleared two compliance checks, quoted a live rate, checked his monthly production,
> and ran an instant underwriting approval check — all without leaving chat.
>
> He never logged into Encompass. He never opened a report. He never put anyone on hold.
>
> For Rate, this means **faster LO response times**, **fewer compliance misses**,
> and loan officers who spend their day closing loans — not chasing data.
>
> **Rate's LOS, pricing engine, compliance records, and document approval engine —
> all surfaced through a single conversation.**

---

## What's Integrated (for technical Q&A)

**`gr-gpt-officer` — Internal LO GPT**

| Data Source | Connected Via | Example |
|---|---|---|
| Rate LOS — full pipeline | `get_lo_pipeline` | 5-loan view, urgency flags, lock status |
| LOS — borrower file | `get_lo_borrower_profile` | Credit, DTI, conditions, UW status |
| Compliance audit trail | `get_loan_compliance_status` | LE/CD dates, TRID window, violations |
| Rate pricing engine | `get_loan_pricing_scenario` | Rate, APR, buydown table, break-even |
| Production reporting | `get_lo_performance_analytics` | Volume, pull-through, referral sources |

**`gpt-simple-demo` — Document Intelligence GPT**

| Data Source | Connected Via | Example |
|---|---|---|
| S3 document store | `get_upload_url` | Presigned upload link, 5-min expiry |
| Auto-approval rule engine | `check_loan_approval` | 10+ UW rules, scored verdict, rule breakdown |
| Approval portal | `get_auto_approval_portal` | Link to `autoapproval.prajnagpt.net` |

---

## Quick Reference — Loan IDs

**`gr-gpt-officer` loans (Scenes 1–3)**

| Loan ID | Borrower | Stage | Key Scenario |
|---|---|---|---|
| `501234001` | Ryan T Chen | Processing | Rate not locked — floating |
| `501234002` | Jamie Torres | Underwriting | 3 conditions open, due Apr 10 |
| `501234003` | James R Kowalski | Conditional Approval | CD not sent, closing Apr 11 ⚠️ |
| `501234004` | Angela S Kim | Clear to Close | Lock Apr 5, closing Apr 4 |
| `501234005` | Derek T Nguyen | Funded | Closed Mar 25, wire confirmed |

**`gpt-simple-demo` loans (Scene 4)**

| Loan ID | Borrower | State | Key Scenario |
|---|---|---|---|
| `123456789` | AZ Borrower | AZ | Purchase — title upload + auto-approval (score 95/105 ✅) |
