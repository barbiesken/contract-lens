"""
parser node — turns raw contract text into a structured list of Clauses.

Strategy:
  1. Heuristic split on numbered headings (1., 1.1, Section 1, Article 1, ALL CAPS HEADERS)
  2. LLM-assisted classification of each clause into one of the 7 checklist categories
  3. Risk pre-scoring (length-based + keyword heuristics for missing-content red flags)
"""

from __future__ import annotations
import re
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from state import Clause, CategoryName, GraphState
from llm import get_llm
from utils.risk_scorer import compute_clause_risk

# Common heading patterns in NDAs / MSAs / SaaS agreements
HEADING_RE = re.compile(
    r"""
    ^(?:
        (?:\d+(?:\.\d+){0,3})\.?\s+[A-Z][A-Za-z\s,/&\-']{2,80}$    # 1.  Indemnification
      | (?:Article|ARTICLE|Section|SECTION|Clause|CLAUSE)\s+\d+    # Section 4 / Article II
        (?:\.\d+){0,2}[\.\s\-:]?\s*[A-Z][A-Za-z\s,/&\-']{0,80}$
      | [A-Z][A-Z\s,/&\-']{4,80}$                                  # ALL CAPS HEADER
    )
    """,
    re.VERBOSE | re.MULTILINE,
)


def heuristic_split(text: str) -> list[Clause]:
    """Splits a contract into rough clauses using heading regex; cheap pre-pass."""
    lines = text.splitlines()
    sections: list[tuple[str, list[str]]] = []  # (heading, [body_lines])
    current_heading = "Preamble"
    current_body: list[str] = []

    for line in lines:
        if HEADING_RE.match(line.strip()):
            if current_body:
                sections.append((current_heading, current_body))
            current_heading = line.strip()
            current_body = []
        else:
            current_body.append(line)
    if current_body:
        sections.append((current_heading, current_body))

    clauses: list[Clause] = []
    for i, (heading, body_lines) in enumerate(sections, 1):
        body = "\n".join(body_lines).strip()
        if not body and len(sections) > 1:
            continue
        clauses.append(Clause(
            id=f"C-{i:02d}",
            heading=heading[:120],
            text=body if body else heading,
        ))
    if not clauses:
        # Fallback — the whole doc as one clause
        clauses.append(Clause(id="C-01", heading="Full Contract", text=text.strip()))
    return clauses


# Pydantic model used as the LLM's structured output target
from pydantic import BaseModel, Field


class ClauseClassification(BaseModel):
    """LLM output: maps each clause id to one of the 7 categories (or null)."""
    clause_id: str
    category: CategoryName | None = Field(
        default=None,
        description="One of the 7 categories or null if the clause is none of these"
    )
    rationale: str = Field(default="", description="Short reason")


class ClassificationBatch(BaseModel):
    classifications: list[ClauseClassification]


CLASSIFY_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "You are a contract analyst. Map each clause to exactly one of these "
     "legal-checklist categories, or null if none apply. Categories: "
     "indemnity, liability, termination, confidentiality, governing_law, "
     "data_protection, ip_assignment. "
     "Be strict — only assign a category if the clause's primary subject matches."),
    ("user",
     "Classify each of the following clauses. Return JSON matching the schema.\n\n"
     "{clauses_block}"),
])


def parser_node(state: GraphState) -> dict[str, Any]:
    """LangGraph node entry point."""
    print(f"[parser] iteration={state.iteration}  parsing contract of length={len(state.original_contract)}")

    clauses = heuristic_split(state.original_contract)

    # Bonus: classify clauses → categories with the LLM
    if clauses and state.original_contract.strip():
        try:
            llm = get_llm(temperature=0.0)
            classifier = llm.with_structured_output(ClassificationBatch, method="function_calling")

            clauses_block = "\n\n".join(
                f"[{c.id}] {c.heading}\n{c.text[:1200]}" for c in clauses
            )
            result: ClassificationBatch = classifier.invoke(
                CLASSIFY_PROMPT.format_messages(clauses_block=clauses_block)
            )
            mapping = {r.clause_id: r.category for r in result.classifications}
            for c in clauses:
                c.category = mapping.get(c.id)
        except Exception as e:
            print(f"[parser] classification skipped due to error: {e}")

    # Bonus: pre-score risk per clause
    for c in clauses:
        c.risk_score = compute_clause_risk(c)

    print(f"[parser] extracted {len(clauses)} clauses; "
          f"categorised {sum(1 for c in clauses if c.category)}")

    return {
        "clauses": clauses,
        "current_draft": state.original_contract,  # iteration-0 draft is the original
    }
