"""
Renders the LangGraph state diagram to assets/graph_diagram.png.

We:
  1. Build the actual graph (build_graph()).
  2. Iterate its nodes and edges (so the diagram stays in sync with the code).
  3. Hand-render via the `graphviz` Python package (calls the `dot` binary).

The output is a publication-quality PNG suitable for the deck and README.

Per Guidelines doc §5: "LangGraph state diagram as PNG or SVG, generated from your
graph (using graph.get_graph().draw_png() or equivalent). This is non-negotiable."
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from graph import build_graph
import graphviz


# -- McKinsey/Bain palette: charcoal, cobalt, amber, slate -------------------
INK = "#0E1628"          # deep slate (titles, lines)
COBALT = "#1F4FD8"       # core nodes
EMBER = "#E0852A"        # critic node (the reflection point)
SLATE = "#475569"        # standard text
CANVAS = "#FAFAFA"       # background
LOOP_RED = "#C0392B"     # the cycle edge
EXIT_GREEN = "#15803D"   # exit edge
GHOST = "#94A3B8"        # start/end terminals


def render(out_png: str = "assets/graph_diagram.png") -> str:
    g = build_graph().get_graph()
    nodes = list(g.nodes.keys())
    edges = list(g.edges)

    # Title as HTML so we can mix sizes/colors. Pass the raw HTML in <...>.
    title_html = (
        '<<font point-size="20" color="' + INK + '"><b>'
        'ContractLens &mdash; Reflection-Loop State Graph</b></font>'
        '<br/><font point-size="11" color="' + SLATE + '">'
        'drafter &#8646; critic cycle &middot; capped at 3 iterations &middot; structured Pydantic feedback'
        '</font>>'
    )

    dot = graphviz.Digraph(
        "ContractLens",
        graph_attr=dict(
            rankdir="TB",
            bgcolor=CANVAS,
            pad="0.6",
            nodesep="0.55",
            ranksep="0.65",
            fontname="Helvetica",
            labelloc="t",
            fontsize="18",
            fontcolor=INK,
        ),
        node_attr=dict(
            shape="box",
            style="rounded,filled",
            fontname="Helvetica",
            fontsize="14",
            fontcolor="white",
            color=INK,
            penwidth="0",
            margin="0.25,0.18",
        ),
        edge_attr=dict(
            fontname="Helvetica",
            fontsize="11",
            color=INK,
            penwidth="1.8",
            arrowsize="0.9",
        ),
    )

    # Apply the HTML title (graphviz's `body` will pass it through verbatim,
    # the leading-< / trailing-> tells the renderer to treat the value as HTML).
    dot.attr(label=title_html)

    # Node specifications --------------------------------------------------
    node_specs = {
        "__start__":  ("Start",      GHOST,   "white"),
        "parser":     ("parser\n— extracts clauses",            COBALT, "white"),
        "drafter":    ("drafter\n— proposes redlines",          COBALT, "white"),
        "critic":     ("critic\n— scores vs 7-point checklist", EMBER,  "white"),
        "formatter":  ("formatter\n— renders final report",     COBALT, "white"),
        "__end__":    ("End",        GHOST,   "white"),
    }

    for n in nodes:
        label, fill, fontcolor = node_specs.get(n, (n, COBALT, "white"))
        # The decision_gate is a *conditional edge*, not a node, in LangGraph.
        # We render it as a diamond inline so the graph reads correctly.
        dot.node(n, label=label, fillcolor=fill, fontcolor=fontcolor,
                 shape="ellipse" if n in ("__start__", "__end__") else "box")

    # Decision-gate diamond (it's a conditional edge function in LangGraph,
    # but readers expect to see the gate explicitly).
    dot.node(
        "decision_gate",
        label="approved\nor iter ≥ 3?",
        shape="diamond",
        fillcolor="#0E1628",
        fontcolor="white",
        style="filled",
        margin="0.05,0.05",
        fontsize="12",
    )

    # Edges ----------------------------------------------------------------
    # Re-route: critic → decision_gate → {drafter, formatter}
    rendered_pairs: set[tuple[str, str]] = set()
    for e in edges:
        src, tgt = e.source, e.target
        if src == "critic" and tgt in ("drafter", "formatter"):
            # We'll render these via decision_gate below
            continue
        rendered_pairs.add((src, tgt))
        dot.edge(src, tgt)

    dot.edge("critic", "decision_gate")
    dot.edge("decision_gate", "drafter",
             label="loop_back  ", color=LOOP_RED, fontcolor=LOOP_RED,
             style="dashed", penwidth="2.0", constraint="false")
    dot.edge("decision_gate", "formatter",
             label="exit", color=EXIT_GREEN, fontcolor=EXIT_GREEN, penwidth="2.0")

    # Render
    out_path = ROOT / out_png
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_stem = str(out_path.with_suffix(""))
    dot.format = "png"
    dot.render(filename=out_stem, cleanup=True)
    print(f"[diagram] wrote {out_path}")

    # Also write SVG (sharper for slides)
    dot.format = "svg"
    dot.render(filename=out_stem, cleanup=True)
    print(f"[diagram] wrote {out_stem}.svg")

    return str(out_path)


if __name__ == "__main__":
    render()
