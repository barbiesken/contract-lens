# Business Memo — ContractLens

**To:** Managing Partner, Meridian Legal LLP
**From:** Group 4, UGDSAI 29 (Masters' Union)
**Re:** First-pass contract review with ContractLens — proposed pilot
**Date:** 1 May 2026

**Live demo:** https://contract-lens.streamlit.app
**Source:** https://github.com/barbiesken/contract-lens

---

## 1. The problem we're solving

Meridian's contract-review function processes ~65 NDAs and service agreements every month. Each one cycles through the same loop: a junior associate drafts redlines, a partner returns comments, the junior revises, and the partner signs off. The pattern is sound; the implementation is not. The loop runs across email inboxes and calendar invites, so the **median round takes four calendar days** for ~12 hours of actual human work — roughly 70% of elapsed time is the partner's review queue. Fully-loaded cost is **~₹ 8,000 per contract** at junior + partner billable rates, and the firm spends roughly **45 senior-partner hours per month** on first-pass review alone.

Three structural pain-points compound the calendar drag: (i) inconsistent first-pass quality from juniors, who apply the same checklist unevenly across deals; (ii) zero institutional memory — language fixed in deal A is re-fought in deal B because the only repository is the partner's head; (iii) no visibility into where time is actually spent, so the firm cannot triage which 20% of clauses warrant senior attention.

## 2. What ContractLens is, in one sentence

ContractLens is a typed agentic loop, built on LangGraph, that runs the same drafter–critic cycle Meridian already uses — but in software, in minutes, against a 7-point legal checklist tuned per jurisdiction (India / US / EU). It produces partner-quality first-pass redlines with rationale, a clause-level risk heat-map, a clean diff against the original, and a full audit log.

Operationally: a junior pastes a contract into the Streamlit UI, picks a jurisdiction and a max-iteration cap, and within ~4 minutes receives a redrafted contract, a CriticVerdict listing every issue with severity and category, and an audit-ready report. The partner reviews the result instead of the raw contract — they spend their time on the 20% of clauses the system flags as HIGH or CRITICAL. A force-approve / force-reject override is built into the workflow so the partner is always the final authority, never displaced by it.

## 3. Why the reflection-loop pattern is the right tool

A linear chain cannot loop conditionally. We considered a nested while-loop in plain Python; it works for a demo and falls apart the moment the firm needs typed state, retry policy, traceability, or human override. LangGraph gives us cycles as a first-class primitive (`add_conditional_edges` from the critic), state as a Pydantic v2 contract (so the critic returns parsed `CriticVerdict` objects, never free text), termination guaranteed by construction (approved=True OR iteration ≥ 3), and full observability via LangSmith with one environment variable. The drafter–critic cycle is exactly the pattern Meridian already uses; we are encoding it, not replacing it.

## 4. Expected impact at Meridian's volume

| KPI | Before | After ContractLens | Movement |
|---|---|---|---|
| Review turnaround | 4 days | ~4 minutes | ~1,400× faster |
| Cost per contract | ₹ 8,000 | ~₹ 100 | ~80× lower |
| Senior-partner hours / month | ~45 h | ~8 h | 82% reclaimed |
| Issues caught vs partner baseline | 1.0× | ~1.4× | +40% recall (estimate) |

Annualised, at 65 contracts × 12 months × ~₹ 7,900 saved per contract, the pilot path opens **~₹ 61.6 lakh / year of recovered margin**, with senior-partner hours redirected to higher-value advisory work and juniors freed from boilerplate redlining. The 1.4× recall figure is our internal estimate, validated against five sample contracts in the test suite; we would not present it externally without held-out validation against partner-marked ground truth, which is on the roadmap.

## 5. Honest limitations

ContractLens is positioned as a **first-pass** tool, not a replacement for senior review. The LLM critic can miss novel clause structures the prompt did not anticipate; the deterministic risk scorer catches obvious red-flags only. We support three jurisdictions today (India, US, EU); state- and member-state-specific quirks are partially abstracted. There is no precedent retrieval yet — the agent does not reuse Meridian's house style across deals. The 3-iteration cap is a heuristic supported by our convergence data; a longer-tail validation set could justify a different cap per contract type.

## 6. Recommendation

Run a four-week pilot on a single deal type — NDAs are the right starting point because they are high-volume, structurally regular, and low-risk. Track the four KPIs above against a matched cohort run through Meridian's existing process. If the pilot replicates the test-suite numbers within 20%, expand to MSAs and DPAs in the second sprint and start scoping the firm-precedent retrieval layer.

---

*Group 4, UGDSAI 29, Masters' Union — Submitted as part of the end-term exam, Problem 4 (Reflection Loop, Legal-tech).*
