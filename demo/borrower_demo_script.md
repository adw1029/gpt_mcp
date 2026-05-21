# Borrower GPT — Demo Script
**Audience:** Executive / President  
**Persona:** Jamie Torres — first-time homebuyer  
**Duration:** ~3 minutes  
**GPT:** `gr-gpt-customer` — `https://1gdypgoned.execute-api.us-east-2.amazonaws.com/mcp`

---

## System Prompt
```
You are Rate's AI mortgage assistant — warm, knowledgeable, and concise.
Help borrowers explore loan options and track their active application.

Demo borrower: Jamie Torres · Loan ID: 501234002
Auto-use this loan ID for any question about "my loan", "my status", "my conditions", etc.
Always call the appropriate tool — never answer loan-specific questions from memory.
```

---

## Opening — Set the Stage (presenter reads aloud)

> Rate is one of the largest retail mortgage lenders in the country —
> over $20B in annual volume, thousands of loan officers, hundreds of thousands of borrowers.
>
> The #1 complaint we hear from borrowers isn't rates. It isn't fees.
> **It's not knowing what's happening with their loan.**
>
> They call their LO. The LO is in three other conversations.
> They email the processor. The processor responds the next day.
> They check the portal. It hasn't been updated since last Tuesday.
>
> What you're about to see is what happens when Rate's entire product catalog,
> live loan data, and LO contact info — all of it — is accessible through a single AI conversation.
>
> No hold music. No ticket. No waiting.

---

## Scene 1 — Discovery: "I don't know where to start" (~60 sec)

*Jamie Torres found Rate.com while researching homes. Never gotten a mortgage before.
Doesn't know what FHA means. Doesn't know their DTI. Just knows their savings and salary.*

**[PROMPT 1]**
> **"Hi! My name is Jamie Torres I found Rate online and I'm trying to figure out if you're the right lender for me. I'm looking at a $320,000 home, I have about $15,000 saved, and my credit score is around 700. What loan programs does Rate offer for someone like me, and what would my monthly payment look like?"**

✅ Tools: `get_loan_products` → `get_rate_quote`

> **What's happening behind the scenes:**
> The AI is calling Rate's live product catalog and rate engine.
> It's not giving a generic answer — it's matching Min's specific profile
> against Rate's actual product set: Conventional, FHA, VA, USDA, Jumbo, ARM.
> It returns a rate, APR, monthly payment, PMI estimate, and a buydown comparison.
> This is the same data a loan officer would pull up on a Saturday morning phone call
> — delivered in under five seconds, at midnight, on a Tuesday.

---

**[PROMPT 2]**
> **"I make about $72,000 a year and I have $950/month in existing debt. First — do I actually qualify for that loan? And second — walk me through exactly how to get pre-approved with Rate and what documents I'll need to pull together."**

✅ Tools: `check_borrower_eligibility` → `get_application_guide`

> **What's happening:**
> Two explicit asks = two tool calls guaranteed.
> First, a real-time DTI calculation (no credit pull) confirms Jamie qualifies and which products fit.
> Then the application guide fires: full document checklist, the 7-stage mortgage process,
> pre-qual vs pre-approval comparison, and a direct link to start the Rate application.
>
> **Talking point for the president:**
> *"What we just replaced was a 30-minute phone call, a follow-up email with a PDF checklist,
> and a two-day wait for a pre-qual letter. Jamie has everything in two messages.
> And critically — the LO didn't have to lift a finger."*

---

## Scene 2 — In Process: "I applied — now what?" (~60 sec)

*Jamie submitted the application. A week has passed. Anxious.
Doesn't know if the underwriter has the file. Doesn't know if the appraisal happened.
Doesn't want to keep bothering the LO.*

**[PROMPT 3]**
> **"I submitted my Rate application last week. I got an email saying it moved to underwriting but I haven't heard anything since. Can you tell me exactly where things stand right now — and has the appraisal been scheduled yet?"**

✅ Tools: `get_loan_status` → `get_appraisal_status`

> **What's happening:**
> Two live queries to Rate's LOS — no screen scraping, no portal login.
> Min sees: Stage 3 of 7, Underwriting, Conditional Approval, assigned underwriter James T.
> Appraisal: ordered through First American AMC, value came in at $318,000, LTV 94.7%, no flags.
>
> She just learned more about her own file in one message than most borrowers learn in a week of emails.

---

**[PROMPT 4]**
> **"I logged into the Rate portal but the conditions list is confusing. Can you just tell me in plain English what's still missing, when it's due, and where I should upload it?"**

✅ Tool: `get_conditions_checklist`

> **What's happening:**
> Live conditions pulled directly from the LOS.
> Two items outstanding: gift letter (due Apr 10), bank statement (due Apr 10).
> One item in review: HOA cert. Each with a secure upload link.
>
> **Talking point:**
> *"The conditions checklist is the #1 source of borrower anxiety and the #1 source of processor
> inbound calls. This is a complete self-service answer. No call. No email. No delay."*

---

## Scene 3 — Closing: "I just need to know the final numbers" (~60 sec)

*Jamie is two weeks from closing. Needs three things:
rate lock details, cash-to-close, and the LO's calendar.*

**[PROMPT 5]**
> **"My closing is coming up and I'm getting nervous about the numbers. What rate did Rate lock me in at, when does it expire, how much do I actually need to bring to the table, and am I going to be paying PMI?"**

✅ Tools: `get_rate_lock_status` → `get_closing_status` → `get_escrow_and_insurance`

> **What's happening:**
> Three separate data systems queried in a single message:
> - Rate lock: 6.750%, APR 6.925%, expires Apr 19 — extension available at 0.125 pts
> - Closing: Apr 18 at Ohio Title, cash-to-close $15,600, CD not yet issued (CTC pending)
> - Escrow: PMI $145/mo (removes at 78% LTV), tax $217, HOI $144, flood zone X — no flood insurance required
>
> **Talking point:**
> *"Three systems. Three questions. One message. This is the kind of answer
> that normally requires a call to the processor, a call to the title company,
> and a follow-up email from the LO. Now it's instant."*

---

**[PROMPT 6]**
> **"After I close, will Rate be servicing my loan or will it get sold off? And I want to hop on a quick call with my Rate loan officer before closing day — can you get me his contact and calendar?"**

✅ Tools: `get_servicing_info` → `get_loan_officer_contact`

> **What's happening:**
> First payment: June 1. Servicer: Guaranteed Rate. Autopay enrollment link surfaced.
> LO card: Andrew Cui — direct phone, email, and a one-click Calendly link.
>
> The AI didn't just answer the question. It handed her the tools to take the next step.

---

## The Close (presenter reads aloud)

> Jamie Torres started this conversation not knowing what FHA meant.
> Three minutes later they knew their loan type, their rate, their monthly payment,
> outstanding conditions with deadlines, cash-to-close, and their LO's calendar link.
>
> She never logged into a portal. She never called anyone. She never waited.
>
> For Rate, this means **fewer inbound calls to processors**,
> **faster time-to-close**, and a borrower experience that turns a stressful process
> into a confident one.
>
> **That is the integration. Rate's data, Rate's products, Rate's people —
> surfaced through a conversation.**

---

## What's Integrated (for technical Q&A)

| Data Source | Connected Via | Example |
|---|---|---|
| Rate product catalog | `get_loan_products` MCP tool | Conventional, FHA, VA, USDA, Jumbo, ARM |
| Live rate engine | `get_rate_quote` MCP tool | Rate, APR, PMI, buydown table |
| Eligibility & DTI logic | `check_borrower_eligibility` MCP tool | Soft pre-qual, doc checklist |
| LOS loan status | `get_loan_status` MCP tool | Stage, underwriter, activity log |
| Appraisal system | `get_appraisal_status` MCP tool | AMC, value, LTV, flags |
| Conditions checklist | `get_conditions_checklist` MCP tool | PTD/PTF items, deadlines, upload link |
| Rate lock system | `get_rate_lock_status` MCP tool | Rate, APR, expiry, extension cost |
| Closing / title | `get_closing_status` MCP tool | Date, location, cash-to-close, CD status |
| Escrow & insurance | `get_escrow_and_insurance` MCP tool | PMI, tax, HOI, flood zone |
| Servicing | `get_servicing_info` MCP tool | First payment, servicer, autopay |
| LO directory | `get_loan_officer_contact` MCP tool | Phone, email, Calendly |

---

## Category Coverage

| Design Doc | Covered By |
|---|---|
| A1 Loan Products | Prompt 1 |
| A2 Rates & Payments | Prompt 1 |
| A3 Eligibility | Prompt 2 |
| A4 Starting Application | Prompt 2 |
| B1 Documents & Conditions | Prompt 4 |
| B2 Closing & Funding | Prompt 5 |
| B3 Rate Lock & Terms | Prompt 5 |
| B4 Contact & Support | Prompt 6 |
| C1 Loan Status (Live) | Prompt 3 |
| C2 Appraisal (Live) | Prompt 3 |
| C3 Conditions (Live) | Prompt 4 |
| C4 Rate Lock (Live) | Prompt 5 |
| C5 Closing (Live) | Prompt 5 |
| C6 Escrow & Insurance | Prompt 5 |
| C7 Servicing | Prompt 6 |
