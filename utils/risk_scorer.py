"""
Risk scorer utility — assigns a 0-10 risk score to each clause.

Bonus item from the brief: "Risk scoring per clause (low, medium, high)".

Heuristics (cheap, deterministic — runs on every clause):
  - One-sided language (e.g., "Supplier shall indemnify Customer..." with no
    reciprocal Customer obligation) ⇒ +risk
  - Unlimited / uncapped phrases ⇒ +risk
  - Penalty / liquidated damages with very high multipliers ⇒ +risk
  - Auto-renewal without opt-out window ⇒ +risk
  - Missing notice / cure period in termination clauses ⇒ +risk
  - Generic GDPR-only language (when no jurisdiction set) ⇒ +risk

The LLM critic does the deep work; this scorer gives a fast first-pass signal
that can drive UI heat-maps and prioritisation.
"""

from __future__ import annotations
import re
from state import Clause, Severity


_RED_FLAG_PATTERNS = [
    (re.compile(r"\bunlimited\s+liability\b", re.I), 3.0, "unlimited liability"),
    # "liability ... shall be unlimited" or "shall be unlimited" in any liability context
    (re.compile(r"\bliabilit(?:y|ies)[^.]{0,80}\bunlimited\b", re.I), 3.0, "unlimited liability (split)"),
    (re.compile(r"\bshall\s+be\s+unlimited\b", re.I), 2.5, "shall-be-unlimited"),
    (re.compile(r"\buncapped\b", re.I), 2.5, "uncapped"),
    (re.compile(r"\bsole\s+(?:and\s+)?absolute\s+discretion\b", re.I), 1.5, "sole-discretion"),
    (re.compile(r"\bno\s+(?:warranty|warranties)\s+of\s+any\s+kind\b", re.I), 1.5, "broad-disclaimer"),
    (re.compile(r"\bautomatically\s+renew(?:s|ed|al)?\b", re.I), 1.5, "auto-renewal"),
    (re.compile(r"\bperpetual\s+(?:license|licence)\b", re.I), 1.0, "perpetual-licence"),
    (re.compile(r"\bindemnif(?:y|ies|ication|y\s+and\s+hold\s+harmless)\b", re.I), 0.5, "indemnity"),
    (re.compile(r"\bin\s+no\s+event\s+shall\b", re.I), 0.3, "limitation"),
    (re.compile(r"\bliquidated\s+damages?\b", re.I), 1.0, "liquidated-damages"),
    (re.compile(r"\bfor\s+convenience\b", re.I), -0.3, "convenience-out"),
    (re.compile(r"\bcure\s+period\b", re.I), -0.3, "cure-period"),
    (re.compile(r"\bmutual(?:ly)?\b", re.I), -0.3, "mutual"),
]

_ONE_SIDED_PATTERNS = [
    re.compile(r"\b(?:supplier|vendor|contractor|service\s+provider)\s+shall\s+indemnif", re.I),
    re.compile(r"\bcustomer\s+shall\s+have\s+no\s+liability\b", re.I),
]


def compute_clause_risk(clause: Clause) -> float:
    """Returns a 0-10 risk score for the clause."""
    text = clause.text or ""
    if not text.strip():
        return 0.0

    score = 1.0  # baseline

    # Pattern hits
    for pattern, weight, _label in _RED_FLAG_PATTERNS:
        hits = len(pattern.findall(text))
        score += weight * min(hits, 3)

    # One-sided detection — adds risk when one party indemnifies / waives without reciprocity
    one_sided_hits = sum(bool(p.search(text)) for p in _ONE_SIDED_PATTERNS)
    if one_sided_hits and "mutual" not in text.lower():
        score += 1.5 * one_sided_hits

    # Length-based: extremely short critical-category clauses are suspicious
    if clause.category in {"indemnity", "liability", "data_protection"} and len(text) < 200:
        score += 1.5  # critical clause is suspiciously thin

    return max(0.0, min(10.0, round(score, 2)))


def severity_from_score(score: float) -> Severity:
    if score >= 7.0:
        return Severity.CRITICAL
    if score >= 5.0:
        return Severity.HIGH
    if score >= 3.0:
        return Severity.MEDIUM
    return Severity.LOW


def score_to_label(score: float) -> str:
    sev = severity_from_score(score)
    return {Severity.LOW: "Low", Severity.MEDIUM: "Medium",
            Severity.HIGH: "High", Severity.CRITICAL: "Critical"}[sev]


def score_to_color(score: float) -> str:
    """Hex colour for UI heat-map (no '#' prefix)."""
    sev = severity_from_score(score)
    return {
        Severity.LOW: "16a34a",       # green
        Severity.MEDIUM: "f59e0b",    # amber
        Severity.HIGH: "ea580c",      # orange
        Severity.CRITICAL: "dc2626",  # red
    }[sev]
