"""
decision_gate — the conditional-edge logic for the reflection loop.

This is THE pattern-specific element the brief tests:
  - if approved OR iteration >= max_iterations → exit to formatter
  - else → loop back to drafter

A hard cap on iterations guards against infinite loops (brief §5).

Note: this is implemented as a router function used by `add_conditional_edges`,
not a graph node. It returns the name of the next node.
"""

from __future__ import annotations
from typing import Literal

from state import GraphState


GateDecision = Literal["loop_back", "exit"]


def decision_gate(state: GraphState) -> GateDecision:
    """
    Router for the conditional edge after the critic node.

    Returns:
      "loop_back" — go back to the drafter for another iteration
      "exit"     — proceed to the formatter and finish the run
    """
    # Bonus: human override takes precedence — partner can force-approve or force-reject
    if state.human_override is True:
        print(f"[decision_gate] human override = APPROVE; exiting at iteration {state.iteration}")
        return "exit"
    if state.human_override is False:
        if state.iteration < state.max_iterations:
            print(f"[decision_gate] human override = REJECT; looping back at iteration {state.iteration}")
            return "loop_back"
        # Even if human says reject, hard cap stops infinite loops
        print("[decision_gate] human override = REJECT but max_iterations reached; exiting")
        return "exit"

    # Normal flow
    if state.approved:
        print(f"[decision_gate] critic approved at iteration {state.iteration}; exiting")
        return "exit"
    if state.iteration >= state.max_iterations:
        print(f"[decision_gate] max_iterations ({state.max_iterations}) reached; exiting")
        return "exit"
    print(f"[decision_gate] not approved (iter {state.iteration}/{state.max_iterations}); looping back")
    return "loop_back"
