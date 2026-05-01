"""
ContractLens - Graph State Schema (Pydantic v2)

Encodes the entire shared memory of the reflection-loop graph.
Every node reads from and writes to this state.
"""

from __future__ import annotations
from datetime import datetime
from typing import Annotated, Literal, Optional
from enum import Enum

from pydantic import BaseModel, Field
from operator import add


# ==========================================================================
# ENUMS
# ==========================================================================

class Severity(str, Enum):
    """Issue severity, drives risk scoring and prioritisation."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Jurisdiction(str, Enum):
    """Supported legal jurisdictions for checklist selection."""
    INDIA = "INDIA"
    US = "US"
    EU = "EU"


class CategoryName(str, Enum):
    """The 7 mandatory legal-checklist categories."""
    INDEMNITY = "indemnity"
    LIABILITY = "liability"
    TERMINATION = "termination"
    CONFIDENTIALITY = "confidentiality"
    GOVERNING_LAW = "governing_law"
    DATA_PROTECTION = "data_protection"
    IP_ASSIGNMENT = "ip_assignment"


# ==========================================================================
# STRUCTURED SUB-MODELS
# ==========================================================================

class Clause(BaseModel):
    """A single parsed clause from the contract."""
    id: str = Field(description="Stable id like 'C-01', 'C-02'")
    heading: str = Field(description="Clause heading (e.g., 'Indemnification')")
    text: str = Field(description="Full clause text")
    category: Optional[CategoryName] = Field(
        default=None,
        description="Mapped checklist category, if any"
    )
    risk_score: float = Field(
        default=0.0,
        ge=0.0, le=10.0,
        description="0-10 risk score; higher = more risk"
    )


class Issue(BaseModel):
    """A single issue raised by the Critic."""
    clause_id: str = Field(description="Which clause this concerns; 'GLOBAL' for whole-contract issues")
    category: CategoryName
    severity: Severity
    description: str = Field(description="Plain-English description of the issue")
    recommendation: str = Field(description="Concrete recommendation for the Drafter")


class Redline(BaseModel):
    """A single proposed redline/change."""
    clause_id: str
    change_type: Literal["INSERT", "DELETE", "REPLACE"]
    original_text: str = Field(default="", description="Text to be removed (DELETE/REPLACE)")
    proposed_text: str = Field(default="", description="Text to be inserted (INSERT/REPLACE)")
    rationale: str = Field(description="Why this change is being made")
    category: CategoryName
    severity: Severity


class CriticVerdict(BaseModel):
    """The Critic's evaluation of the current draft."""
    approved: bool = Field(description="True if the draft passes; loop terminates")
    overall_risk: Severity
    issues: list[Issue] = Field(default_factory=list)
    summary: str = Field(description="One-paragraph overall summary")
    coverage: dict[str, bool] = Field(
        default_factory=dict,
        description="Which of the 7 categories were adequately addressed"
    )


class IterationRecord(BaseModel):
    """Snapshot of one drafter→critic round for audit / UI."""
    iteration: int
    timestamp: datetime = Field(default_factory=datetime.now)
    redlines: list[Redline] = Field(default_factory=list)
    critic_verdict: Optional[CriticVerdict] = None
    drafter_strategy_note: str = Field(default="", description="What the drafter changed this round")


# ==========================================================================
# GRAPH STATE (the brief's mandatory schema, plus bonus fields)
# ==========================================================================

class GraphState(BaseModel):
    """
    The single source of truth for the reflection loop.

    Required fields (per brief §4.2):
      original_contract, clauses, current_draft, critic_feedback,
      iteration, approved, final_output

    Bonus fields are added below the divider.
    """

    # --- Brief-mandated fields ------------------------------------------------
    original_contract: str = Field(default="", description="Raw contract text uploaded by the user")
    clauses: list[Clause] = Field(default_factory=list)
    current_draft: str = Field(default="", description="Latest drafter output (full marked-up contract)")
    critic_feedback: list[Issue] = Field(default_factory=list)
    iteration: int = Field(default=0, ge=0)
    approved: bool = Field(default=False)
    final_output: str = Field(default="")

    # --- Configuration --------------------------------------------------------
    jurisdiction: Jurisdiction = Field(default=Jurisdiction.INDIA)
    max_iterations: int = Field(default=3, ge=1, le=5)
    enabled_categories: list[CategoryName] = Field(
        default_factory=lambda: list(CategoryName),
        description="Configurable from the UI; minimum 7 categories supported"
    )

    # --- Bonus / observability fields ----------------------------------------
    redlines: list[Redline] = Field(
        default_factory=list,
        description="All redlines accepted into the final draft (for rationale rendering)"
    )
    iteration_history: list[IterationRecord] = Field(
        default_factory=list,
        description="Full audit log; powers the side-by-side UI"
    )
    critic_verdict: Optional[CriticVerdict] = Field(
        default=None,
        description="Latest critic verdict (used by decision_gate)"
    )
    human_override: Optional[bool] = Field(
        default=None,
        description="If a human partner overrides the critic verdict, recorded here"
    )
    human_override_reason: str = Field(default="")
    started_at: datetime = Field(default_factory=datetime.now)

    # Pydantic v2 config
    model_config = {
        "arbitrary_types_allowed": True,
        "validate_assignment": True,
    }
