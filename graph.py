"""
ContractLens — LangGraph wiring.

Topology:

       ┌─────────┐
       │ parser  │
       └────┬────┘
            ↓
       ┌─────────┐
   ┌──→│ drafter │
   │   └────┬────┘
   │        ↓
   │   ┌─────────┐
   │   │ critic  │
   │   └────┬────┘
   │        ↓
   │   ┌─────────────────┐
   │   │ decision_gate   │  (conditional edge)
   │   └────┬────────────┘
   │        ├── loop_back ─┐
   │        └── exit       │
   │                       ↓
   │                  ┌──────────┐
   └──────────────────│ formatter│
                      └────┬─────┘
                           ↓
                          END

The cycle drafter → critic → drafter is the brief's mandatory
"true cycle with termination condition" requirement.
"""

from __future__ import annotations
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from state import GraphState
from nodes.parser import parser_node
from nodes.drafter import drafter_node
from nodes.critic import critic_node
from nodes.decision_gate import decision_gate
from nodes.formatter import formatter_node


def build_graph(use_checkpointer: bool = False):
    """Build and compile the ContractLens reflection-loop graph."""
    workflow = StateGraph(GraphState)

    workflow.add_node("parser", parser_node)
    workflow.add_node("drafter", drafter_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("formatter", formatter_node)

    # Linear setup
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "drafter")
    workflow.add_edge("drafter", "critic")

    # The conditional edge is the heart of the reflection pattern:
    workflow.add_conditional_edges(
        "critic",
        decision_gate,
        {
            "loop_back": "drafter",   # cycle back for another iteration
            "exit": "formatter",      # exit the loop
        },
    )
    workflow.add_edge("formatter", END)

    if use_checkpointer:
        return workflow.compile(checkpointer=MemorySaver())
    return workflow.compile()


def run_contract_lens(
    contract_text: str,
    jurisdiction: str = "INDIA",
    max_iterations: int = 3,
    enabled_categories: list[str] | None = None,
) -> GraphState:
    """Convenience runner — used by the CLI and the test suite."""
    from state import Jurisdiction, CategoryName

    initial = GraphState(
        original_contract=contract_text,
        jurisdiction=Jurisdiction(jurisdiction),
        max_iterations=max_iterations,
        enabled_categories=(
            [CategoryName(c) for c in enabled_categories]
            if enabled_categories else list(CategoryName)
        ),
    )
    graph = build_graph()
    final_state = graph.invoke(initial)
    if isinstance(final_state, dict):
        return GraphState(**final_state)
    return final_state


def export_graph_diagram(out_path: str = "assets/graph_diagram.png") -> str:
    """
    Saves the LangGraph state diagram as a PNG.

    Per the Guidelines doc: "graph.get_graph().draw_png() ... is non-negotiable —
    it is the single best indicator of whether the team understands the framework."
    """
    import os
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    graph = build_graph()
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open(out_path, "wb") as f:
            f.write(png_bytes)
        print(f"[graph] diagram saved to {out_path}")
        return out_path
    except Exception as e:
        # Fallback to mermaid text
        mermaid = graph.get_graph().draw_mermaid()
        out_md = out_path.rsplit(".", 1)[0] + ".mmd"
        with open(out_md, "w") as f:
            f.write(mermaid)
        print(f"[graph] PNG export failed ({e}); wrote mermaid source to {out_md}")
        return out_md


if __name__ == "__main__":
    export_graph_diagram()
