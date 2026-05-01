"""
ContractLens — Streamlit UI.

Implements every brief-mandated component plus all bonus features:
  ✓ Visible iteration counter
  ✓ Side-by-side draft and critic issues per iteration
  ✓ Configurable 7-category checklist (categories toggleable in sidebar)
  ✓ Hard cap on iterations
  ✓ Rationale for every accepted change
  ✓ Bonus: jurisdiction-specific checklists (India / US / EU)
  ✓ Bonus: risk scoring per clause
  ✓ Bonus: diff view between original and final
  ✓ Bonus: human-in-the-loop partner override
  ✓ Bonus: download buttons for marked-up contract & full report

Run:  streamlit run app.py
"""

from __future__ import annotations
import io
import os
import time
from datetime import datetime
from pathlib import Path

import streamlit as st

from state import GraphState, Jurisdiction, CategoryName, Severity
from graph import build_graph
from llm import get_provider_info
from utils.diff_viewer import render_html_diff, render_unified_diff, count_changes
from utils.risk_scorer import score_to_color, score_to_label

# --------------------------------------------------------------------------
# Page config & global CSS
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ContractLens — Reflection-Loop Contract Reviewer",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root {
    --cl-primary: #0f172a;
    --cl-accent: #0891b2;
    --cl-success: #15803d;
    --cl-warning: #b45309;
    --cl-danger: #b91c1c;
    --cl-muted: #64748b;
    --cl-border: #e2e8f0;
    --cl-surface: #ffffff;
    --cl-surface-2: #f8fafc;
}

/* Header strip */
.cl-hero {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 12px;
    margin-bottom: 1.5rem;
}
.cl-hero h1 { color: white; margin: 0; font-weight: 700; letter-spacing: -0.5px;}
.cl-hero p  { color: #cbd5e1; margin: 0.4rem 0 0 0; font-size: 0.95rem;}
.cl-hero-meta { display: inline-block; background: rgba(8,145,178,0.18); border: 1px solid rgba(8,145,178,0.4); padding: 2px 10px; border-radius: 6px; font-size: 0.8rem; margin-right: 6px; }

/* KPI cards */
.cl-kpi {
    background: var(--cl-surface);
    border: 1px solid var(--cl-border);
    border-radius: 10px;
    padding: 14px 18px;
    height: 100%;
}
.cl-kpi-label { color: var(--cl-muted); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 4px;}
.cl-kpi-value { color: var(--cl-primary); font-size: 1.8rem; font-weight: 700; line-height: 1;}
.cl-kpi-foot { color: var(--cl-muted); font-size: 0.78rem; margin-top: 6px; }

/* Issue cards */
.cl-issue {
    border-left: 4px solid var(--cl-muted);
    background: var(--cl-surface);
    padding: 10px 14px;
    border-radius: 6px;
    margin-bottom: 8px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.05);
}
.cl-issue-CRITICAL { border-left-color: var(--cl-danger); }
.cl-issue-HIGH     { border-left-color: #ea580c; }
.cl-issue-MEDIUM   { border-left-color: var(--cl-warning); }
.cl-issue-LOW      { border-left-color: var(--cl-success); }

.cl-issue-head { display:flex; gap:6px; align-items:center; margin-bottom: 4px; }
.cl-tag { font-size: 0.7rem; padding: 1px 8px; border-radius: 12px; background: #f1f5f9; color: #475569; border: 1px solid #e2e8f0;}
.cl-tag-CRITICAL { background: #fee2e2; color: #b91c1c; border-color: #fecaca;}
.cl-tag-HIGH     { background: #ffedd5; color: #c2410c; border-color: #fed7aa;}
.cl-tag-MEDIUM   { background: #fef3c7; color: #b45309; border-color: #fde68a;}
.cl-tag-LOW      { background: #dcfce7; color: #166534; border-color: #bbf7d0;}

.cl-iteration-pill { background: var(--cl-accent); color: white; padding: 2px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 600; }

/* Side-by-side panel */
.cl-panel { background: var(--cl-surface-2); padding: 12px 14px; border-radius: 8px; border: 1px solid var(--cl-border); height: 100%; }
.cl-panel h4 { margin: 0 0 8px 0; color: var(--cl-primary); font-size: 0.95rem; }

/* Status badge */
.cl-badge { display:inline-block; padding: 4px 12px; border-radius: 999px; font-weight:600; font-size: 0.85rem; }
.cl-badge-approved { background: #dcfce7; color: #166534;}
.cl-badge-failed   { background: #fef3c7; color: #92400e;}
.cl-badge-running  { background: #e0f2fe; color: #075985;}

/* Risk pill */
.cl-risk { display: inline-block; padding: 1px 8px; border-radius: 6px; font-size:0.72rem; color:white; font-weight:600; }

/* Section headers */
.cl-section { font-size: 1.1rem; font-weight: 700; color: var(--cl-primary); margin: 1rem 0 0.5rem 0;}

/* Override Streamlit defaults a touch */
.block-container { padding-top: 1.2rem; max-width: 1500px; }
[data-testid="stSidebar"] { background: #f8fafc; }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Session state initialisation
# --------------------------------------------------------------------------
def _init_session():
    defaults = {
        "result_state": None,
        "is_running": False,
        "logs": [],
        "human_override": None,
        "human_override_reason": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_session()


# --------------------------------------------------------------------------
# Sidebar — configuration
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Configuration")
    provider_info = None
    try:
        provider_info = get_provider_info()
    except Exception as e:
        st.error(f"⚠️ {e}")

    if provider_info:
        st.caption(f"**Engine:** {provider_info['provider']} · `{provider_info['model']}`")

    st.markdown("---")

    jurisdiction = st.selectbox(
        "Jurisdiction",
        options=[j.value for j in Jurisdiction],
        index=0,
        help="Drives the legal checklist used by the critic and drafter.",
    )

    max_iter = st.slider(
        "Max iterations (hard cap)",
        min_value=1, max_value=5, value=3,
        help="The reflection loop terminates after this many drafter→critic cycles "
             "even if the critic still has issues. Brief mandates a hard cap to "
             "prevent infinite loops."
    )

    st.markdown("**Legal checklist categories**")
    st.caption("Toggle the 7+ categories the critic should evaluate.")
    enabled_cats = []
    for cat in CategoryName:
        default = True
        if st.checkbox(
            cat.value.replace("_", " ").title(),
            value=default,
            key=f"cat_{cat.value}",
        ):
            enabled_cats.append(cat)

    st.markdown("---")
    st.markdown("### 🧑‍⚖️ Partner Override (HITL)")
    st.caption(
        "Bonus: the partner can pre-set an override before running. "
        "Force-approve skips the loop after the first round; force-reject extends iterations."
    )
    override_choice = st.radio(
        "Override mode",
        options=["No override", "Force approve", "Force reject"],
        index=0,
    )
    override_reason = ""
    if override_choice != "No override":
        override_reason = st.text_input("Reason", placeholder="e.g., partner accepts critic findings")


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="cl-hero">
        <h1>⚖️ ContractLens</h1>
        <p>Reflection-loop contract reviewer · Drafter ⇄ Critic until partner-quality</p>
        <div style="margin-top: 10px;">
            <span class="cl-hero-meta">LangGraph</span>
            <span class="cl-hero-meta">Pydantic v2</span>
            <span class="cl-hero-meta">{provider_info['provider'] if provider_info else 'LLM'}</span>
            <span class="cl-hero-meta">Jurisdiction: {jurisdiction}</span>
            <span class="cl-hero-meta">Cap: {max_iter} iter</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Input section
# --------------------------------------------------------------------------
st.markdown("#### 📄 Contract input")
input_tab, sample_tab = st.tabs(["Paste / Upload", "Use a sample"])

contract_text = ""
with input_tab:
    file = st.file_uploader("Upload a contract (.txt / .md)", type=["txt", "md"])
    if file:
        contract_text = file.read().decode("utf-8", errors="ignore")
        st.success(f"Loaded {file.name} — {len(contract_text):,} chars")
    pasted = st.text_area(
        "...or paste contract text here",
        height=180,
        placeholder="Paste a draft NDA, MSA, SaaS agreement, etc.",
        value=contract_text if not file else "",
    )
    if pasted and not file:
        contract_text = pasted

with sample_tab:
    sample_dir = Path(__file__).parent / "data"
    if sample_dir.exists():
        samples = sorted([p for p in sample_dir.glob("*.txt") if p.is_file()])
        if samples:
            choice = st.selectbox("Sample contracts", options=[s.name for s in samples])
            sample_path = sample_dir / choice
            sample_text = sample_path.read_text(encoding="utf-8", errors="ignore")
            with st.expander("Preview"):
                st.code(sample_text[:3000] + ("\n…" if len(sample_text) > 3000 else ""), language="text")
            if st.button("Load this sample", key="load_sample"):
                contract_text = sample_text
                st.session_state["loaded_sample"] = sample_text
                st.rerun()
    if "loaded_sample" in st.session_state and not contract_text:
        contract_text = st.session_state["loaded_sample"]


# --------------------------------------------------------------------------
# Run controls
# --------------------------------------------------------------------------
col_run, col_clear = st.columns([1, 5])
with col_run:
    run_btn = st.button(
        "▶ Run reflection loop",
        type="primary",
        disabled=(not contract_text.strip() or st.session_state["is_running"]),
        use_container_width=True,
    )
with col_clear:
    if st.button("🗑 Clear results"):
        st.session_state["result_state"] = None
        st.session_state["logs"] = []
        st.rerun()


# --------------------------------------------------------------------------
# Run the graph
# --------------------------------------------------------------------------
def _override_to_state(choice: str) -> bool | None:
    return {"Force approve": True, "Force reject": False}.get(choice)


def _execute_graph():
    st.session_state["is_running"] = True
    st.session_state["logs"] = []

    initial_state = GraphState(
        original_contract=contract_text,
        jurisdiction=Jurisdiction(jurisdiction),
        max_iterations=max_iter,
        enabled_categories=enabled_cats or list(CategoryName),
        human_override=_override_to_state(override_choice),
        human_override_reason=override_reason,
    )

    graph = build_graph()
    progress = st.progress(0.0, text="Starting reflection loop...")
    status_box = st.empty()
    log_box = st.empty()
    logs = []

    expected_steps = 2 + max_iter * 2 + 1  # parser + N*(drafter+critic) + formatter (rough)
    step = 0
    final_state_dict: dict | None = None

    try:
        for event in graph.stream(initial_state.model_dump(), stream_mode="updates"):
            for node_name, partial_update in event.items():
                step += 1
                logs.append(f"✓ `{node_name}` ran at {datetime.now().strftime('%H:%M:%S')}")
                progress.progress(min(step / expected_steps, 0.99),
                                  text=f"Running `{node_name}`...")
                # Show a richer status line
                if node_name == "drafter":
                    iter_now = partial_update.get("iteration", "?")
                    n_redlines = len(partial_update.get("redlines", []))
                    status_box.markdown(
                        f"📝 **Drafter** finished iteration {iter_now} — "
                        f"{n_redlines} redlines proposed."
                    )
                elif node_name == "critic":
                    approved = partial_update.get("approved", False)
                    n_issues = len(partial_update.get("critic_feedback", []))
                    status_box.markdown(
                        f"🔍 **Critic** evaluated draft — approved={approved}, {n_issues} issues."
                    )
                log_box.markdown("\n".join(f"- {l}" for l in logs[-8:]))
                # Capture latest state by merging
                if final_state_dict is None:
                    final_state_dict = dict(initial_state.model_dump())
                final_state_dict.update(partial_update)
        progress.progress(1.0, text="Done.")
        if final_state_dict is not None:
            st.session_state["result_state"] = GraphState(**final_state_dict)
        st.session_state["logs"] = logs
    except Exception as e:
        st.error(f"Graph failed: {e}")
        import traceback
        st.code(traceback.format_exc())
    finally:
        st.session_state["is_running"] = False


if run_btn and contract_text.strip():
    _execute_graph()


# --------------------------------------------------------------------------
# Render results
# --------------------------------------------------------------------------
result: GraphState | None = st.session_state.get("result_state")

if result is None:
    st.info("Configure the run in the sidebar, paste a contract, then press **Run reflection loop**.")
    st.markdown("---")
    st.markdown("### 🧱 Architecture at a glance")
    st.markdown("""
    1. **parser** — splits the contract into clauses, classifies each into one of 7 categories, and assigns a heuristic risk score (0-10).
    2. **drafter** — proposes redlines; on iteration ≥ 2, reads the previous critic's structured feedback so each cycle improves the draft.
    3. **critic** — evaluates the draft against a jurisdiction-specific 7-point checklist; produces a structured `CriticVerdict` with approved/issues/coverage.
    4. **decision_gate** — conditional edge: loop back if not approved AND iterations remain; else exit.
    5. **formatter** — produces the final marked-up contract with a rationale for every redline, an audit trail, and a coverage map.
    """)
    st.stop()


# ---- KPI strip ----
n_iter = result.iteration
n_redlines = len(result.redlines)
n_critical = sum(1 for i in result.critic_feedback if i.severity == Severity.CRITICAL)
n_high = sum(1 for i in result.critic_feedback if i.severity == Severity.HIGH)
duration = (datetime.now() - result.started_at).total_seconds()
diff_stats = count_changes(result.original_contract, result.current_draft)
total_issues_open = len(result.critic_feedback)
total_categories = len(result.enabled_categories)
covered = sum(1 for ok in (result.critic_verdict.coverage if result.critic_verdict else {}).values() if ok)

kpi_cols = st.columns(6)
with kpi_cols[0]:
    badge = ("approved" if result.approved else
             ("failed" if n_iter >= result.max_iterations else "running"))
    txt = "Approved" if result.approved else (f"Cap reached" if n_iter >= result.max_iterations else "Running")
    st.markdown(
        f'<div class="cl-kpi"><div class="cl-kpi-label">Status</div>'
        f'<div class="cl-kpi-value"><span class="cl-badge cl-badge-{badge}">{txt}</span></div>'
        f'<div class="cl-kpi-foot">Iter {n_iter}/{result.max_iterations}</div></div>',
        unsafe_allow_html=True,
    )
with kpi_cols[1]:
    st.markdown(
        f'<div class="cl-kpi"><div class="cl-kpi-label">Iterations</div>'
        f'<div class="cl-kpi-value">{n_iter}</div>'
        f'<div class="cl-kpi-foot">drafter ⇄ critic</div></div>',
        unsafe_allow_html=True,
    )
with kpi_cols[2]:
    st.markdown(
        f'<div class="cl-kpi"><div class="cl-kpi-label">Redlines</div>'
        f'<div class="cl-kpi-value">{n_redlines}</div>'
        f'<div class="cl-kpi-foot">accepted into draft</div></div>',
        unsafe_allow_html=True,
    )
with kpi_cols[3]:
    st.markdown(
        f'<div class="cl-kpi"><div class="cl-kpi-label">Open issues</div>'
        f'<div class="cl-kpi-value">{total_issues_open}</div>'
        f'<div class="cl-kpi-foot">{n_critical} critical · {n_high} high</div></div>',
        unsafe_allow_html=True,
    )
with kpi_cols[4]:
    st.markdown(
        f'<div class="cl-kpi"><div class="cl-kpi-label">Coverage</div>'
        f'<div class="cl-kpi-value">{covered}/{total_categories}</div>'
        f'<div class="cl-kpi-foot">categories satisfied</div></div>',
        unsafe_allow_html=True,
    )
with kpi_cols[5]:
    st.markdown(
        f'<div class="cl-kpi"><div class="cl-kpi-label">Wall-clock</div>'
        f'<div class="cl-kpi-value">{duration:.0f}s</div>'
        f'<div class="cl-kpi-foot">{diff_stats["total"]} line edits</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")


# ---- Tabs for the rest ----
tab_loop, tab_clauses, tab_redlines, tab_diff, tab_final, tab_audit = st.tabs([
    "🔁 Reflection Loop",
    "📑 Clause map (risk)",
    "✏️  Redlines",
    "📊 Diff (orig → final)",
    "📋 Final report",
    "🧾 Audit log",
])


# ----- Tab 1: Reflection loop side-by-side per iteration -----
with tab_loop:
    if not result.iteration_history:
        st.info("No iterations recorded.")
    else:
        st.caption("Each row shows what the drafter produced and how the critic responded.")
        for rec in result.iteration_history:
            v = rec.critic_verdict
            verdict_label = "✅ Approved" if (v and v.approved) else "❌ Not approved"
            badge_cls = "cl-badge-approved" if (v and v.approved) else "cl-badge-failed"
            st.markdown(
                f'<div style="display:flex; gap:10px; align-items:center; margin: 12px 0 8px 0;">'
                f'<span class="cl-iteration-pill">Iteration {rec.iteration}</span> '
                f'<span class="cl-badge {badge_cls}">{verdict_label}</span> '
                f'<span style="color:#64748b; font-size:0.85rem;">'
                f'· {len(rec.redlines)} redlines proposed · '
                f'{len(v.issues) if v else 0} issues raised'
                f'</span></div>',
                unsafe_allow_html=True,
            )
            left, right = st.columns(2)
            with left:
                st.markdown('<div class="cl-panel"><h4>📝 Drafter strategy & redlines</h4>',
                            unsafe_allow_html=True)
                st.markdown(f"_{rec.drafter_strategy_note or 'No strategy note recorded.'}_")
                if rec.redlines:
                    st.markdown(f"**{len(rec.redlines)} redlines** in this iteration:")
                    for i, r in enumerate(rec.redlines[:8], 1):
                        st.markdown(
                            f'<div class="cl-issue cl-issue-{r.severity.value}">'
                            f'<div class="cl-issue-head">'
                            f'<span class="cl-tag cl-tag-{r.severity.value}">{r.severity.value}</span>'
                            f'<span class="cl-tag">{r.category.value}</span>'
                            f'<span class="cl-tag">{r.clause_id}</span>'
                            f'<span class="cl-tag">{r.change_type}</span></div>'
                            f'<div style="font-size:0.85rem;">{r.rationale}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    if len(rec.redlines) > 8:
                        st.caption(f"… and {len(rec.redlines) - 8} more.")
                st.markdown("</div>", unsafe_allow_html=True)
            with right:
                st.markdown('<div class="cl-panel"><h4>🔍 Critic verdict & issues</h4>',
                            unsafe_allow_html=True)
                if v:
                    st.markdown(f"**Overall risk:** "
                                f'<span class="cl-tag cl-tag-{v.overall_risk.value}">{v.overall_risk.value}</span>',
                                unsafe_allow_html=True)
                    st.markdown(f"_{v.summary}_")
                    if v.issues:
                        st.markdown(f"**Issues raised:**")
                        for issue in v.issues[:8]:
                            st.markdown(
                                f'<div class="cl-issue cl-issue-{issue.severity.value}">'
                                f'<div class="cl-issue-head">'
                                f'<span class="cl-tag cl-tag-{issue.severity.value}">{issue.severity.value}</span>'
                                f'<span class="cl-tag">{issue.category.value}</span>'
                                f'<span class="cl-tag">{issue.clause_id}</span></div>'
                                f'<div style="font-weight:600; font-size:0.88rem;">{issue.description}</div>'
                                f'<div style="font-size:0.82rem; color:#64748b; margin-top: 4px;">'
                                f'→ {issue.recommendation}</div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        if len(v.issues) > 8:
                            st.caption(f"… and {len(v.issues) - 8} more.")
                    else:
                        st.success("No issues raised.")
                else:
                    st.info("No verdict recorded.")
                st.markdown("</div>", unsafe_allow_html=True)


# ----- Tab 2: Clause map with risk -----
with tab_clauses:
    st.caption("Each clause classified into one of 7 categories with a 0-10 risk score (heuristic + LLM).")
    if not result.clauses:
        st.info("No clauses extracted.")
    else:
        for c in result.clauses:
            cat = c.category.value if c.category else "—"
            color = score_to_color(c.risk_score)
            label = score_to_label(c.risk_score)
            st.markdown(
                f'<div class="cl-issue" style="border-left-color: #{color};">'
                f'<div class="cl-issue-head">'
                f'<span class="cl-tag" style="background:#{color}; color:white; border-color:#{color};">{label} risk · {c.risk_score:.1f}/10</span>'
                f'<span class="cl-tag">{c.id}</span>'
                f'<span class="cl-tag">{cat}</span></div>'
                f'<div style="font-weight:600;">{c.heading}</div>'
                f'<div style="font-size:0.82rem; color:#64748b; margin-top: 4px;">'
                f'{c.text[:300]}{"..." if len(c.text) > 300 else ""}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


# ----- Tab 3: Redlines -----
with tab_redlines:
    st.caption("All redlines accepted into the final draft, with rationale per change (brief §5).")
    if not result.redlines:
        st.info("No redlines proposed.")
    else:
        # Group by category
        by_cat: dict[str, list] = {}
        for r in result.redlines:
            by_cat.setdefault(r.category.value, []).append(r)
        for cat, rs in sorted(by_cat.items()):
            st.markdown(f"##### {cat.replace('_', ' ').title()} ({len(rs)} redlines)")
            for r in rs:
                with st.expander(f"[{r.severity.value}] {r.clause_id} · {r.change_type}"):
                    if r.original_text:
                        st.markdown("**Original**")
                        st.code(r.original_text, language="text")
                    if r.proposed_text:
                        st.markdown("**Proposed**")
                        st.code(r.proposed_text, language="text")
                    st.markdown("**Rationale**")
                    st.markdown(f"_{r.rationale}_")


# ----- Tab 4: Diff -----
with tab_diff:
    st.caption("Bonus: side-by-side diff between the original and the final marked-up contract.")
    diff_html = render_html_diff(result.original_contract, result.current_draft)
    st.components.v1.html(diff_html, height=700, scrolling=True)
    udiff = render_unified_diff(result.original_contract, result.current_draft)
    st.download_button(
        "⬇ Download unified diff (.patch)",
        data=udiff,
        file_name=f"contractlens_diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.patch",
        mime="text/x-patch",
    )


# ----- Tab 5: Final report -----
with tab_final:
    st.markdown(result.final_output)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            "⬇ Download final report (.md)",
            data=result.final_output,
            file_name=f"contractlens_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
        )
    with col_d2:
        st.download_button(
            "⬇ Download marked-up contract (.txt)",
            data=result.current_draft,
            file_name=f"contractlens_revised_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
        )


# ----- Tab 6: Audit log -----
with tab_audit:
    st.caption("Every node invocation, in order, with timestamps. For Q&A and reproducibility.")
    if st.session_state["logs"]:
        for log in st.session_state["logs"]:
            st.markdown(f"- {log}")
    else:
        st.info("No logs from the most recent run (try re-running).")
    with st.expander("Raw GraphState (JSON)"):
        st.json(result.model_dump(mode="json"), expanded=False)
