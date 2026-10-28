# Demo Workflow Guide

A reference for loan officers and demo users. Copy-paste any prompt directly into the chat.

---

## 1. Look Up a Loan

**What it does:** Fetches core loan fields — amount, status, property, loan officer, borrower names.

> "Look up loan 123456789"

> "What is the loan amount and status for loan 123456789?"

> "Who is the loan officer on loan 123456789?"

---

## 2. Get the Borrower's Client Profile

**What it does:** Pulls the borrower's background, full loan history, and peer reviews from other loan officers.

> "Tell me about the borrower on loan 123456789"

> "What do other loan officers say about this client?"

> "Give me the client profile for loan 123456789"

---

## 3. Full Loan Intelligence Briefing

**What it does:** One-shot executive briefing — loan overview + borrower rating + auto-approval readiness scores + market context + risk flags + recommended next step.

> "Brief me on loan 123456789"

> "Give me the full picture on loan 123456789"

> "Run a full intelligence report on loan 123456789"

---

## 4. OneLoan Data Lookup

**What it does:** Fetches live document extraction data from the OneLoan LOS. Searches all organizations automatically (GRI, GRA, KBHS, Citywide, OriginPoint, Premia, PR).

> "Get the OneLoan data for loan 265561631"

> "What does OneLoan say about loan 265561631?"

> "Pull the OneLoan record for loan 265561631"

---

## 5. Start a New Mortgage Application

**What it does:** Walks through a 13-field mortgage application conversationally, then returns a DMX reference number and pre-qualification analysis (DTI, LTV, recommended loan type).

> "I want to start a new mortgage application for my client"

> "Let's fill out a mortgage application for a new borrower"

> "Begin a DMX mortgage application"

The assistant will ask one question at a time:
1. Full legal name
2. Date of birth
3. Property address
4. Property type *(Single-family / Condo / Townhouse / Multi-family)*
5. Intended use *(Primary residence / Second home / Investment)*
6. Loan purpose *(Purchase / Refinance / Cash-out Refinance)*
7. Purchase price or home value
8. Requested loan amount
9. Employment status *(W-2 / Self-employed / Retired / Other)*
10. Gross annual income
11. Existing monthly debt payments
12. Liquid assets / savings
13. Credit score range

---

## 6. Check an Existing Application Status

**What it does:** Looks up a previously submitted DMX application by borrower name (partial, case-insensitive).

> "What is the status of Andy's mortgage application?"

> "Find the DMX application for Andy Smith"

> "What was the reference number for Andy's application?"

---

## 7. Speak with a Live Virtual Agent

**What it does:** Returns the link to the live avatar-based mortgage agent for voice or text chat.

> "I want to speak with a live agent"

> "Connect me with a virtual mortgage specialist"

> "Can I talk to someone about my application?"

---

## 8. Upload a Document for Auto-Approval

**What it does:** Generates a secure 5-minute upload link. The loan officer opens it in a browser, drags and drops a PDF, and the system automatically runs the approval check after upload.

> "I want to upload a document for loan 123456789"

> "Give me an upload link for loan 123456789"

> "I need to submit a title document for loan 123456789"

---

## 9. Run Auto-Approval Check

**What it does:** Runs the scoring engine immediately (no upload needed). Returns a scored verdict with rule-by-rule breakdown, LTV, state risk, and OneLoan data enrichment.

### Quick check (instant, rule-based)

> "Run a quick title approval check for loan 123456789"

> "Check insurance approval for loan 123456789"

> "Is loan 123456789 eligible for auto-approval?"

> "I've uploaded the document — now check the approval for loan 123456789"

### Thorough check (full portal)

> "Do a thorough approval review for loan 123456789"

> "I want a deep review on loan 123456789 — send me to the portal"

---

## 10. Full Auto-Approval Dashboard

**What it does:** Opens the complete web-based auto-approval portal with full underwriting tools.

> "Open the auto-approval dashboard for loan 123456789"

> "Take me to the full approval portal for loan 123456789"

> "I want to see the complete approval dashboard — loan 123456789"

🔗 Portal: [https://autoapproval.prajnagpt.net/login](https://autoapproval.prajnagpt.net/login)

---

## Quick Reference

| Goal | Best prompt |
|---|---|
| Single field lookup | "What is the [field] for loan [ID]?" |
| Full briefing | "Brief me on loan [ID]" |
| Client background | "Tell me about the borrower on loan [ID]" |
| OneLoan data | "Get the OneLoan data for loan [ID]" |
| New application | "Start a new mortgage application" |
| Application status | "Find the DMX application for [name]" |
| Live agent | "I want to speak with a live agent" |
| Upload document | "Give me an upload link for loan [ID]" |
| Quick approval | "Run a quick title approval check for loan [ID]" |
| Thorough approval | "Do a thorough approval review for loan [ID]" |
| Approval portal | "Open the auto-approval dashboard for loan [ID]" |

---

## Demo Loan IDs

| Loan ID | Borrower | State | Amount | Notes |
|---|---|---|---|---|
| `123456789` | Alex T. Rivera | AZ | $320,000 | Purchase, Detached, HOA flag |
| `265561631` | John A. Homeowner | IL | $400,000 | Purchase, Detached, clean profile |
| `319847205` | Maria L. Reyes | TX | $275,000 | Refinance, Attached |
| `408823917` | David K. Park | CA | $650,000 | Purchase, Jumbo, New construction |
