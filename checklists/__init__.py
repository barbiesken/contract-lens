"""
Checklist registry — single source of truth for jurisdiction → checklist mapping.
"""

from __future__ import annotations
from typing import Any

from state import Jurisdiction
from checklists.india import INDIA_CHECKLIST
from checklists.us import US_CHECKLIST
from checklists.eu import EU_CHECKLIST


CHECKLISTS: dict[Jurisdiction, list[dict[str, Any]]] = {
    Jurisdiction.INDIA: INDIA_CHECKLIST,
    Jurisdiction.US: US_CHECKLIST,
    Jurisdiction.EU: EU_CHECKLIST,
}


def get_checklist(jurisdiction: Jurisdiction, enabled_categories: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Returns the (filtered) checklist for the given jurisdiction.

    If `enabled_categories` is provided, only items whose `category` field is in
    that list are returned. Otherwise the full checklist is returned.
    """
    full = CHECKLISTS[jurisdiction]
    if not enabled_categories:
        return full
    enabled_set = {c.value if hasattr(c, "value") else c for c in enabled_categories}
    return [item for item in full if item["category"] in enabled_set]


def render_checklist_for_prompt(jurisdiction: Jurisdiction, enabled_categories: list[str] | None = None) -> str:
    """
    Renders the checklist as a structured text block for inclusion in LLM prompts.
    """
    items = get_checklist(jurisdiction, enabled_categories)
    out: list[str] = [f"### Legal checklist — Jurisdiction: {jurisdiction.value}\n"]
    for i, item in enumerate(items, 1):
        out.append(f"\n**{i}. {item['title']} ({item['category']})**")
        out.append("MUST HAVE:")
        for m in item["must_have"]:
            out.append(f"  - {m}")
        out.append("MUST AVOID:")
        for m in item["must_avoid"]:
            out.append(f"  - {m}")
        if item.get("statutory_hooks"):
            out.append("STATUTORY HOOKS:")
            for s in item["statutory_hooks"]:
                out.append(f"  - {s}")
    return "\n".join(out)
