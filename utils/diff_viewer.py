"""
Diff viewer utility — produces a clean side-by-side diff between original and final
contract text. Bonus from the brief: "Diff view between original and final".
"""

from __future__ import annotations
from difflib import HtmlDiff, unified_diff


def render_unified_diff(original: str, revised: str, n_context: int = 2) -> str:
    """Plain-text unified diff string (good for download / log)."""
    diff = unified_diff(
        original.splitlines(keepends=False),
        revised.splitlines(keepends=False),
        fromfile="original.txt",
        tofile="revised.txt",
        n=n_context,
        lineterm="",
    )
    return "\n".join(diff)


def render_html_diff(original: str, revised: str, context: bool = True) -> str:
    """Side-by-side HTML diff (used by Streamlit via st.components.v1.html)."""
    differ = HtmlDiff(wrapcolumn=80, tabsize=2)
    html = differ.make_table(
        original.splitlines(),
        revised.splitlines(),
        fromdesc="Original",
        todesc="Revised",
        context=context,
        numlines=3,
    )
    # Style the default difflib output for a clean modern look
    style = """
    <style>
      table.diff { font-family: 'JetBrains Mono', Consolas, Menlo, monospace;
                   font-size: 12px; border-collapse: collapse; width: 100%; }
      .diff_header { background-color:#0f172a; color:#fff; padding:4px 8px; }
      td.diff_header { text-align:right; color:#94a3b8; background:#f1f5f9; }
      .diff_next { background-color:#e2e8f0; }
      .diff_add { background-color:#dcfce7; }
      .diff_chg { background-color:#fef9c3; }
      .diff_sub { background-color:#fee2e2; }
      td { padding: 2px 6px; vertical-align: top; }
    </style>
    """
    return style + html


def count_changes(original: str, revised: str) -> dict[str, int]:
    """Summary stats for the UI badge."""
    diff_lines = list(unified_diff(
        original.splitlines(),
        revised.splitlines(),
        n=0,
        lineterm="",
    ))
    additions = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
    deletions = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
    return {"added": additions, "deleted": deletions, "total": additions + deletions}
