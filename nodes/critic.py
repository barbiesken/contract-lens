"""
critic node — evaluates the current draft against the configured legal checklist.

Outputs a structured CriticVerdict with:
  - approved (bool) — drives the loop-termination conditional edge
  - issues (list[Issue]) — fed back into the next drafter iteration
  - coverage map — which checklist categories the draft addresses adequately

The critic must produce STRUCTURED output (not free text), per the brief's
pattern-specific requirement. We use Pydantic + with_structured_output().
"""

from __future__ import annotations
from typing import Any

from langchain_core.prompts import ChatPromptTemplate

from state import GraphState, CriticVerdict, IterationRecord
from llm import get_llm
from checklists import render_checklist_for_prompt


SYSTEM_PROMPT = """You are a senior contracts partner conducting a final review. You evaluate the draft against a strict legal checklist and return a structured verdict.

Verdict criteria:
  - APPROVED only if the draft is at partner-quality: every checklist category is adequately addressed, no critical or high-severity issues remain
  - For each issue, supply a specific, actionable recommendation a junior associate could implement
  - Be calibrated, not exhaustive — surface the highest-impact issues first; cap at 8 issues
  - Map each issue to one of the checklist categories
  - Mark coverage[category] = True only if you would sign off on that category as-is

Severity rubric:
  CRITICAL — blocks signing (e.g., uncapped one-sided indemnity)
  HIGH     — material commercial risk (e.g., missing breach-notification timeline)
  MEDIUM   — should be fixed but not a blocker (e.g., minor governing-law ambiguity)
  LOW      — stylistic / clean-up (e.g., defined term used inconsistently)

Always write your `summary` so a partner could read it in 30 seconds."""

USER_TEMPLATE = """## Jurisdiction
{jurisdiction}

## Iteration number
{iteration}

## Legal checklist (the standard you are evaluating against)
{checklist}

## Current draft (drafter iteration {iteration})
```
{draft}
```

Return your structured verdict now. The `coverage` field must be a dict mapping each enabled category name to true/false."""


def critic_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node entry. Critiques state.current_draft."""
    print(f"[critic] evaluating draft from iteration {state.iteration}")

    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(CriticVerdict)

    checklist_block = render_checklist_for_prompt(
        state.jurisdiction,
        [c.value if hasattr(c, "value") else c for c in state.enabled_categories],
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("user", USER_TEMPLATE),
    ])
    messages = prompt.format_messages(
        jurisdiction=state.jurisdiction.value,
        iteration=state.iteration,
        checklist=checklist_block,
        draft=state.current_draft,
    )

    verdict: CriticVerdict = structured_llm.invoke(messages)

    print(f"[critic] approved={verdict.approved} | issues={len(verdict.issues)} | "
          f"overall_risk={verdict.overall_risk.value}")

    # Update the latest iteration record with the verdict
    history = list(state.iteration_history)
    if history:
        history[-1] = IterationRecord(
            iteration=history[-1].iteration,
            timestamp=history[-1].timestamp,
            redlines=history[-1].redlines,
            critic_verdict=verdict,
            drafter_strategy_note=history[-1].drafter_strategy_note,
        )

    return {
        "critic_verdict": verdict,
        "critic_feedback": verdict.issues,
        "approved": verdict.approved,
        "iteration_history": history,
    }
