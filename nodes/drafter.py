"""
drafter node — proposes redlines.

Iteration 1: drafts cold (jurisdiction-aware, checklist-driven).
Iteration ≥ 2: drafts with the previous critic's structured feedback threaded in,
               so each cycle produces a meaningfully different draft.
"""

from __future__ import annotations
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from state import GraphState, Redline, IterationRecord, CategoryName, Severity, Issue
from llm import get_llm
from checklists import render_checklist_for_prompt


# --------------------------------------------------------------------------
# Structured output schemas
# --------------------------------------------------------------------------
class DrafterOutput(BaseModel):
    """The drafter's structured output for one full pass."""
    revised_contract: str = Field(
        description="The full revised contract with all redlines incorporated, "
                    "as a single text block ready for legal review"
    )
    redlines: list[Redline] = Field(
        default_factory=list,
        description="Each individual change with rationale"
    )
    drafter_strategy_note: str = Field(
        default="",
        description="One-paragraph note on the drafter's strategy for this iteration "
                    "(e.g. what they prioritised, what feedback they incorporated)"
    )


# --------------------------------------------------------------------------
# Prompt templates
# --------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a senior contract drafter at a top-tier corporate law firm. Your task is to propose redlines (revisions) to a client contract so that it passes a strict legal-quality checklist.

You produce:
  1. A full revised contract with your changes folded in
  2. A list of individual redlines with rationale, severity, and category mapping

Drafting principles:
  - Make targeted, surgical changes — don't rewrite the entire contract
  - Each redline must clearly fix a specific deficiency
  - Use precise legal language consistent with the chosen jurisdiction
  - Stay within standard market practice; don't gold-plate
  - Be explicit about what you ARE changing and what you are deliberately leaving alone
  - Cap your work at 12-18 redlines per pass — focus on the highest-leverage issues first

Critically: do not invent facts or parties not present in the contract. Only propose changes the contract's content can support."""

ITERATION_1_USER = """## Jurisdiction
{jurisdiction}

## Legal checklist you must satisfy
{checklist}

## Original contract
```
{contract}
```

## Identified clauses (parser output)
{clauses_summary}

Produce the structured drafter output now. Focus on the categories enabled in the checklist above. Cap at 18 redlines."""

ITERATION_N_USER = """## Jurisdiction
{jurisdiction}

## Legal checklist you must satisfy
{checklist}

## Your previous draft (iteration {prev_iter})
```
{prev_draft}
```

## Critic's feedback on the previous draft
The critic identified the following remaining issues. Address each one specifically. Do not regress on points the critic already approved.

{critic_feedback_block}

## Critic's overall summary
{critic_summary}

## Strategy for this iteration
- Re-use the prior draft as your base (don't restart)
- For each issue above, produce a targeted redline that resolves it
- If you disagree with a critic point, you may keep your prior text but state your reasoning in the rationale
- In your `drafter_strategy_note`, briefly explain what you changed and why

Produce the structured drafter output now."""


def _format_clauses_summary(clauses: list[Any]) -> str:
    if not clauses:
        return "(no parsed clauses)"
    rows = []
    for c in clauses[:30]:
        cat = c.category.value if c.category else "—"
        rows.append(f"- [{c.id}] cat={cat} risk={c.risk_score:.1f} | {c.heading[:80]}")
    if len(clauses) > 30:
        rows.append(f"... and {len(clauses) - 30} more")
    return "\n".join(rows)


def _format_critic_feedback(issues: list[Issue]) -> str:
    if not issues:
        return "(none)"
    rows = []
    for i, issue in enumerate(issues, 1):
        rows.append(
            f"{i}. [{issue.severity.value}] [{issue.category.value}] (clause {issue.clause_id})\n"
            f"   Issue: {issue.description}\n"
            f"   Recommendation: {issue.recommendation}"
        )
    return "\n\n".join(rows)


# --------------------------------------------------------------------------
# Node entry point
# --------------------------------------------------------------------------
def drafter_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node entry. Reads state.iteration to pick the right prompt path."""
    iteration_num = state.iteration + 1
    print(f"[drafter] starting iteration {iteration_num}")

    llm = get_llm(temperature=0.1)
    structured_llm = llm.with_structured_output(DrafterOutput)

    checklist_block = render_checklist_for_prompt(
        state.jurisdiction,
        [c.value if hasattr(c, "value") else c for c in state.enabled_categories],
    )

    if iteration_num == 1:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", ITERATION_1_USER),
        ])
        messages = prompt.format_messages(
            jurisdiction=state.jurisdiction.value,
            checklist=checklist_block,
            contract=state.original_contract,
            clauses_summary=_format_clauses_summary(state.clauses),
        )
    else:
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("user", ITERATION_N_USER),
        ])
        prev_critic = state.critic_verdict
        messages = prompt.format_messages(
            jurisdiction=state.jurisdiction.value,
            checklist=checklist_block,
            prev_iter=state.iteration,
            prev_draft=state.current_draft,
            critic_feedback_block=_format_critic_feedback(state.critic_feedback),
            critic_summary=prev_critic.summary if prev_critic else "(none)",
        )

    output: DrafterOutput = structured_llm.invoke(messages)

    print(f"[drafter] produced {len(output.redlines)} redlines for iteration {iteration_num}")
    print(f"[drafter] strategy note: {output.drafter_strategy_note[:160]}")

    # Append iteration record (keep prior records intact)
    new_record = IterationRecord(
        iteration=iteration_num,
        redlines=output.redlines,
        drafter_strategy_note=output.drafter_strategy_note,
    )
    history = state.iteration_history + [new_record]

    return {
        "current_draft": output.revised_contract,
        "redlines": output.redlines,           # latest iteration's redlines (cumulative view in formatter)
        "iteration": iteration_num,
        "iteration_history": history,
    }
