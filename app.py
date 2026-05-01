"""
ContractLens — Streamlit UI.

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
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="ContractLens · Legal AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Global CSS — premium legal-tech, dark, locked-in
# --------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Cormorant+Garamond:wght@500;700&display=swap');

:root {
    --cl-bg:          #0A0E1A;
    --cl-surface-1:   #0F1623;
    --cl-surface-2:   #141C2E;
    --cl-surface-3:   #1A2540;
    --cl-border:      #1E2A44;
    --cl-border-soft: #2A3656;
    --cl-text:        #E5E9F0;
    --cl-text-muted:  #94A3B8;
    --cl-text-dim:    #64748B;
    --cl-accent:      #3B82F6;
    --cl-accent-deep: #1F4FD8;
    --cl-accent-glow: rgba(59,130,246,0.18);
    --cl-gold:        #D4AF37;
    --cl-gold-soft:   rgba(212,175,55,0.15);
    --cl-success:     #10B981;
    --cl-warning:     #F59E0B;
    --cl-danger:      #EF4444;
    --cl-orange:      #FB923C;
    --cl-mono: 'JetBrains Mono', 'SF Mono', Menlo, Consolas, monospace;
    --cl-sans: 'Inter', -apple-system, BlinkMacSystemFont, system-ui, sans-serif;
    --cl-serif: 'Cormorant Garamond', Georgia, serif;
}

html, body, .stApp, [data-testid="stAppViewContainer"] {
    background: var(--cl-bg) !important;
    color: var(--cl-text) !important;
    font-family: var(--cl-sans);
}

header[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stToolbar"] { right: 1rem; }
#MainMenu, footer { visibility: hidden; }

.stApp::before {
    content: ""; position: fixed; inset: 0; pointer-events: none;
    background-image:
        radial-gradient(circle at 25% 0%, rgba(59,130,246,0.08), transparent 40%),
        radial-gradient(circle at 75% 100%, rgba(212,175,55,0.05), transparent 40%);
    z-index: 0;
}

.block-container {
    padding-top: 1.5rem !important; padding-bottom: 3rem !important;
    max-width: 1500px; position: relative; z-index: 1;
}

h1, h2, h3, h4, h5 {
    color: var(--cl-text) !important;
    font-family: var(--cl-sans);
    font-weight: 700;
    letter-spacing: -0.015em;
}
.stMarkdown p, .stMarkdown li { color: var(--cl-text); line-height: 1.55; }
.stMarkdown code {
    background: var(--cl-surface-2) !important;
    color: var(--cl-accent) !important;
    border: 1px solid var(--cl-border);
    padding: 1px 6px; border-radius: 4px;
    font-family: var(--cl-mono); font-size: 0.85em;
}

/* SIDEBAR — locked dark */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F1623 0%, #0A0E1A 100%) !important;
    border-right: 1px solid var(--cl-border) !important;
}
[data-testid="stSidebar"] > div:first-child {
    background: transparent !important;
    padding-top: 1rem;
}
[data-testid="stSidebar"] *, [data-testid="stSidebar"] p, [data-testid="stSidebar"] label,
[data-testid="stSidebar"] span, [data-testid="stSidebar"] div {
    color: var(--cl-text) !important;
}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h4 {
    color: var(--cl-text) !important; font-weight: 700;
}
[data-testid="stSidebar"] .stCaption,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
    color: var(--cl-text-muted) !important;
}
[data-testid="stSidebar"] hr { border-color: var(--cl-border) !important; margin: 0.8rem 0 !important; }

[data-testid="stSidebar"] [data-baseweb="select"] > div,
[data-testid="stSidebar"] [data-baseweb="input"] > div,
[data-testid="stSidebar"] [data-baseweb="textarea"] > div {
    background: var(--cl-surface-2) !important;
    border-color: var(--cl-border) !important;
    color: var(--cl-text) !important;
}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {
    background: var(--cl-surface-2) !important;
    color: var(--cl-text) !important;
    caret-color: var(--cl-accent) !important;
}
[data-testid="stSidebar"] input::placeholder,
[data-testid="stSidebar"] textarea::placeholder {
    color: var(--cl-text-dim) !important;
}
[data-testid="stSidebar"] [data-baseweb="checkbox"] > div:first-child,
[data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
    background: var(--cl-surface-2) !important;
    border-color: var(--cl-border-soft) !important;
}
[data-testid="stSidebar"] [data-baseweb="checkbox"][aria-checked="true"] > div:first-child,
[data-testid="stSidebar"] [data-baseweb="radio"][aria-checked="true"] > div:first-child {
    background: var(--cl-accent) !important;
    border-color: var(--cl-accent) !important;
}
[data-testid="stSidebar"] [data-baseweb="slider"] [role="slider"] {
    background: var(--cl-accent) !important;
    box-shadow: 0 0 0 4px rgba(59,130,246,0.18) !important;
}

[data-baseweb="popover"] [role="listbox"] {
    background: var(--cl-surface-2) !important;
    border: 1px solid var(--cl-border) !important;
}
[data-baseweb="popover"] [role="option"] { color: var(--cl-text) !important; }
[data-baseweb="popover"] [role="option"]:hover { background: var(--cl-surface-3) !important; }

[data-testid="collapsedControl"] {
    background: var(--cl-surface-2) !important;
    border: 1px solid var(--cl-border) !important;
    border-radius: 8px !important;
    color: var(--cl-accent) !important;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
[data-testid="collapsedControl"]:hover {
    background: var(--cl-surface-3) !important;
    border-color: var(--cl-accent) !important;
}

/* Main inputs */
.stTextArea textarea, .stTextInput input {
    background: var(--cl-surface-1) !important;
    color: var(--cl-text) !important;
    border: 1px solid var(--cl-border) !important;
    border-radius: 8px !important;
    font-family: var(--cl-sans);
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: var(--cl-accent) !important;
    box-shadow: 0 0 0 3px var(--cl-accent-glow) !important;
}
.stTextArea textarea::placeholder { color: var(--cl-text-dim) !important; }
[data-baseweb="select"] > div {
    background: var(--cl-surface-1) !important;
    border-color: var(--cl-border) !important;
    color: var(--cl-text) !important;
}

/* Buttons */
.stButton > button {
    background: var(--cl-surface-2) !important;
    color: var(--cl-text) !important;
    border: 1px solid var(--cl-border-soft) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.15s ease;
}
.stButton > button:hover {
    background: var(--cl-surface-3) !important;
    border-color: var(--cl-accent) !important;
    color: var(--cl-accent) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--cl-accent) 0%, var(--cl-accent-deep) 100%) !important;
    color: #ffffff !important;
    border: 1px solid var(--cl-accent) !important;
    box-shadow: 0 4px 14px var(--cl-accent-glow);
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(59,130,246,0.35);
}
.stDownloadButton > button {
    background: var(--cl-surface-2) !important;
    color: var(--cl-gold) !important;
    border: 1px solid var(--cl-gold-soft) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stDownloadButton > button:hover {
    background: var(--cl-gold-soft) !important;
    border-color: var(--cl-gold) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--cl-border) !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--cl-text-muted) !important;
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 18px !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--cl-text) !important;
    background: var(--cl-surface-1) !important;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    color: var(--cl-accent) !important;
    background: var(--cl-surface-1) !important;
    box-shadow: inset 0 -2px 0 var(--cl-accent);
}

/* Expander */
.streamlit-expanderHeader, [data-testid="stExpander"] summary {
    background: var(--cl-surface-1) !important;
    color: var(--cl-text) !important;
    border: 1px solid var(--cl-border) !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
[data-testid="stExpander"] {
    background: var(--cl-surface-1);
    border: 1px solid var(--cl-border);
    border-radius: 8px;
}

/* File uploader */
[data-testid="stFileUploader"] section {
    background: var(--cl-surface-1) !important;
    border: 1px dashed var(--cl-border-soft) !important;
    border-radius: 10px !important;
    color: var(--cl-text-muted) !important;
}
[data-testid="stFileUploader"] section:hover { border-color: var(--cl-accent) !important; }

/* Alerts */
[data-testid="stAlert"] {
    background: var(--cl-surface-1) !important;
    border: 1px solid var(--cl-border) !important;
    border-radius: 8px !important;
    color: var(--cl-text) !important;
}
[data-testid="stAlert"][kind="info"]    { border-left: 3px solid var(--cl-accent) !important; }
[data-testid="stAlert"][kind="success"] { border-left: 3px solid var(--cl-success) !important; }
[data-testid="stAlert"][kind="warning"] { border-left: 3px solid var(--cl-warning) !important; }
[data-testid="stAlert"][kind="error"]   { border-left: 3px solid var(--cl-danger) !important; }

/* Progress bar */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, var(--cl-accent) 0%, var(--cl-gold) 100%) !important;
}
.stProgress > div > div { background: var(--cl-surface-2) !important; }

/* Code blocks */
pre, .stCodeBlock, [data-testid="stCodeBlock"] {
    background: var(--cl-surface-1) !important;
    border: 1px solid var(--cl-border) !important;
    border-radius: 8px !important;
}
pre code, .stCodeBlock code { color: var(--cl-text) !important; font-family: var(--cl-mono) !important; }

/* CUSTOM COMPONENTS */

/* Hero */
.cl-hero {
    background: linear-gradient(135deg, #0F1623 0%, #1A2540 100%);
    border: 1px solid var(--cl-border);
    border-radius: 16px;
    padding: 2rem 2.4rem;
    margin: 0.5rem 0 1.5rem 0;
    position: relative; overflow: hidden;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
}
.cl-hero::before {
    content: ""; position: absolute;
    top: -50%; right: -10%;
    width: 500px; height: 500px;
    background: radial-gradient(circle, var(--cl-accent-glow) 0%, transparent 60%);
    pointer-events: none;
}
.cl-hero::after {
    content: ""; position: absolute;
    bottom: 0; left: 0; width: 100%; height: 1px;
    background: linear-gradient(90deg, transparent 0%, var(--cl-accent) 50%, transparent 100%);
}
.cl-hero-row { display: flex; align-items: center; gap: 1rem; position: relative; z-index: 1; }
.cl-hero-mark {
    width: 56px; height: 56px; border-radius: 14px;
    background: linear-gradient(135deg, var(--cl-accent) 0%, var(--cl-accent-deep) 100%);
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
    box-shadow: 0 4px 16px var(--cl-accent-glow);
    flex-shrink: 0;
}
.cl-hero h1 {
    color: var(--cl-text) !important;
    margin: 0 !important;
    font-size: 2.2rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    line-height: 1.1 !important;
}
.cl-hero-tag {
    color: var(--cl-gold);
    font-family: var(--cl-serif);
    font-style: italic;
    font-size: 1.05rem;
    margin-top: 4px;
    font-weight: 500;
}
.cl-hero p {
    color: var(--cl-text-muted) !important;
    margin: 0.7rem 0 0 0 !important;
    font-size: 0.95rem;
    max-width: 720px;
}
.cl-pills {
    display: flex; flex-wrap: wrap; gap: 8px;
    margin-top: 1.1rem; position: relative; z-index: 1;
}
.cl-pill {
    background: var(--cl-surface-3);
    border: 1px solid var(--cl-border-soft);
    color: var(--cl-text-muted);
    font-size: 0.78rem;
    padding: 4px 11px;
    border-radius: 999px;
    font-family: var(--cl-mono);
    font-weight: 500;
    letter-spacing: 0.02em;
}
.cl-pill-live {
    background: rgba(16,185,129,0.1);
    border-color: rgba(16,185,129,0.3);
    color: var(--cl-success);
}
.cl-pill-live::before {
    content: "●";
    margin-right: 4px;
    animation: pulse 1.8s ease-in-out infinite;
}
@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.35; }
}

/* KPI cards */
.cl-kpi {
    background: var(--cl-surface-1);
    border: 1px solid var(--cl-border);
    border-radius: 12px;
    padding: 16px 18px;
    height: 100%;
    transition: all 0.2s ease;
    position: relative; overflow: hidden;
}
.cl-kpi:hover {
    border-color: var(--cl-border-soft);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.25);
}
.cl-kpi::before {
    content: ""; position: absolute;
    top: 0; left: 0; width: 3px; height: 100%;
    background: var(--cl-accent); opacity: 0.7;
}
.cl-kpi-label {
    color: var(--cl-text-dim);
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 8px;
    font-weight: 600;
    font-family: var(--cl-mono);
}
.cl-kpi-value {
    color: var(--cl-text);
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.02em;
}
.cl-kpi-foot {
    color: var(--cl-text-muted);
    font-size: 0.78rem;
    margin-top: 8px;
}

/* Issue cards */
.cl-issue {
    background: var(--cl-surface-1);
    border: 1px solid var(--cl-border);
    border-left: 3px solid var(--cl-text-dim);
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 8px;
    transition: all 0.15s ease;
    color: var(--cl-text);
}
.cl-issue:hover {
    background: var(--cl-surface-2);
    border-color: var(--cl-border-soft);
}
.cl-issue-CRITICAL { border-left-color: var(--cl-danger); }
.cl-issue-HIGH     { border-left-color: var(--cl-orange); }
.cl-issue-MEDIUM   { border-left-color: var(--cl-warning); }
.cl-issue-LOW      { border-left-color: var(--cl-success); }
.cl-issue-head {
    display: flex; gap: 6px; align-items: center;
    margin-bottom: 6px; flex-wrap: wrap;
}

/* Tags */
.cl-tag {
    font-size: 0.68rem;
    padding: 2px 9px;
    border-radius: 6px;
    background: var(--cl-surface-2);
    color: var(--cl-text-muted);
    border: 1px solid var(--cl-border);
    font-family: var(--cl-mono);
    font-weight: 500;
    letter-spacing: 0.03em;
}
.cl-tag-CRITICAL { background: rgba(239,68,68,0.15);  color: #FCA5A5; border-color: rgba(239,68,68,0.3); }
.cl-tag-HIGH     { background: rgba(251,146,60,0.15); color: #FDBA74; border-color: rgba(251,146,60,0.3); }
.cl-tag-MEDIUM   { background: rgba(245,158,11,0.15); color: #FCD34D; border-color: rgba(245,158,11,0.3); }
.cl-tag-LOW      { background: rgba(16,185,129,0.15); color: #6EE7B7; border-color: rgba(16,185,129,0.3); }

/* Iteration pill */
.cl-iteration-pill {
    background: linear-gradient(135deg, var(--cl-accent) 0%, var(--cl-accent-deep) 100%);
    color: white;
    padding: 4px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    box-shadow: 0 2px 8px var(--cl-accent-glow);
}

/* Side-by-side panel */
.cl-panel {
    background: var(--cl-surface-1);
    padding: 16px 18px;
    border-radius: 12px;
    border: 1px solid var(--cl-border);
    height: 100%;
}
.cl-panel h4 {
    margin: 0 0 12px 0 !important;
    color: var(--cl-text) !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    padding-bottom: 10px;
    border-bottom: 1px solid var(--cl-border);
}

/* Status badge */
.cl-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-size: 0.82rem;
    font-family: var(--cl-mono);
    letter-spacing: 0.04em;
}
.cl-badge-approved {
    background: rgba(16,185,129,0.15);
    color: var(--cl-success);
    border: 1px solid rgba(16,185,129,0.3);
}
.cl-badge-failed {
    background: rgba(245,158,11,0.15);
    color: var(--cl-warning);
    border: 1px solid rgba(245,158,11,0.3);
}
.cl-badge-running {
    background: var(--cl-accent-glow);
    color: var(--cl-accent);
    border: 1px solid rgba(59,130,246,0.3);
}

/* Section divider */
.cl-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent 0%, var(--cl-border-soft) 50%, transparent 100%);
    margin: 1.5rem 0;
}

/* Empty state */
.cl-empty {
    background: var(--cl-surface-1);
    border: 1px solid var(--cl-border);
    border-radius: 16px;
    padding: 2.5rem;
    margin-top: 1rem;
    position: relative; overflow: hidden;
}
.cl-empty::before {
    content: ""; position: absolute;
    top: -100px; right: -100px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, var(--cl-accent-glow) 0%, transparent 60%);
}
.cl-empty h3 {
    color: var(--cl-text) !important;
    margin: 0 0 8px 0 !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}
.cl-empty-tag {
    color: var(--cl-gold);
    font-family: var(--cl-mono);
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 12px;
    display: block;
}
.cl-flow-step {
    display: flex; gap: 14px;
    padding: 12px 0;
    border-top: 1px solid var(--cl-border);
}
.cl-flow-step:first-of-type { border-top: none; }
.cl-flow-num {
    flex-shrink: 0;
    width: 32px; height: 32px;
    border-radius: 8px;
    background: var(--cl-surface-2);
    border: 1px solid var(--cl-border-soft);
    color: var(--cl-accent);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--cl-mono);
    font-weight: 700;
    font-size: 0.85rem;
}
.cl-flow-body strong { color: var(--cl-text); font-size: 0.95rem; }
.cl-flow-body p {
    color: var(--cl-text-muted) !important;
    margin: 4px 0 0 0 !important;
    font-size: 0.88rem;
}

/* Section title */
.cl-section-title {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: var(--cl-accent);
    font-family: var(--cl-mono);
    font-weight: 600;
    margin: 1.5rem 0 0.5rem 0;
}
.cl-section-h {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--cl-text);
    letter-spacing: -0.02em;
    margin: 0 0 1rem 0;
}

/* Iteration row header */
.cl-iter-row {
    display: flex; gap: 12px; align-items: center;
    margin: 1.5rem 0 0.8rem 0;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--cl-border);
}

/* Sidebar brand */
.cl-side-brand {
    font-family: var(--cl-serif);
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--cl-text);
    letter-spacing: -0.02em;
    margin: 0;
}
.cl-side-brand-tag {
    font-family: var(--cl-mono);
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    color: var(--cl-gold);
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}
.cl-side-section {
    font-family: var(--cl-mono);
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    color: var(--cl-accent);
    text-transform: uppercase;
    font-weight: 600;
    margin: 1.2rem 0 0.5rem 0;
}
.cl-engine-card {
    background: var(--cl-surface-2);
    border: 1px solid var(--cl-border);
    border-radius: 10px;
    padding: 10px 12px;
    margin: 1rem 0 0.5rem 0;
}
.cl-engine-row { display: flex; align-items: center; gap: 8px; }
.cl-engine-dot {
    width: 8px; height: 8px;
    border-radius: 50%;
    background: var(--cl-success);
    box-shadow: 0 0 8px var(--cl-success);
    animation: pulse 1.8s ease-in-out infinite;
    flex-shrink: 0;
}
.cl-engine-dot.off { background: var(--cl-danger); box-shadow: 0 0 8px var(--cl-danger); }
.cl-engine-name { color: var(--cl-text); font-weight: 700; font-size: 0.88rem; }
.cl-engine-model {
    color: var(--cl-text-muted);
    font-family: var(--cl-mono);
    font-size: 0.75rem;
    margin-top: 2px;
}

.element-container { margin-bottom: 0.4rem; }
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Session state
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
# Sidebar
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="cl-side-brand-tag">⚖️ LEGAL · AI</div>'
        '<p class="cl-side-brand">ContractLens</p>',
        unsafe_allow_html=True,
    )

    provider_info = None
    err_msg = None
    try:
        provider_info = get_provider_info()
    except Exception as e:
        err_msg = str(e)

    if provider_info and provider_info.get("ready"):
        st.markdown(
            f'<div class="cl-engine-card">'
            f'<div class="cl-engine-row">'
            f'<span class="cl-engine-dot"></span>'
            f'<div>'
            f'<div class="cl-engine-name">{provider_info["provider"]}</div>'
            f'<div class="cl-engine-model">{provider_info["model"]}</div>'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="cl-engine-card">'
            '<div class="cl-engine-row">'
            '<span class="cl-engine-dot off"></span>'
            '<div>'
            '<div class="cl-engine-name">No engine</div>'
            '<div class="cl-engine-model">Set API key in .env</div>'
            '</div></div></div>',
            unsafe_allow_html=True,
        )
        if err_msg:
            st.caption(f"⚠️ {err_msg}")

    st.markdown('<div class="cl-side-section">Run Configuration</div>', unsafe_allow_html=True)

    jurisdiction = st.selectbox(
        "Jurisdiction",
        options=[j.value for j in Jurisdiction],
        index=0,
        help="Drives the legal checklist used by the critic and drafter.",
    )

    max_iter = st.slider(
        "Max iterations",
        min_value=1, max_value=5, value=3,
        help="Hard cap on the reflection loop.",
    )

    st.markdown('<div class="cl-side-section">Checklist Categories</div>', unsafe_allow_html=True)
    st.caption("Toggle which of the 7 legal categories the critic evaluates.")

    enabled_cats = []
    for cat in CategoryName:
        if st.checkbox(
            cat.value.replace("_", " ").title(),
            value=True,
            key=f"cat_{cat.value}",
        ):
            enabled_cats.append(cat)

    st.markdown('<div class="cl-side-section">Partner Override · HITL</div>', unsafe_allow_html=True)
    st.caption("Force-approve skips the loop after the first round; force-reject extends iterations.")
    override_choice = st.radio(
        "Override mode",
        options=["No override", "Force approve", "Force reject"],
        index=0,
        label_visibility="collapsed",
    )
    override_reason = ""
    if override_choice != "No override":
        override_reason = st.text_input(
            "Reason",
            placeholder="e.g., partner accepts critic findings",
        )


# --------------------------------------------------------------------------
# Hero
# --------------------------------------------------------------------------
engine_label = provider_info["provider"] if (provider_info and provider_info.get("ready")) else "Offline"
engine_state = "cl-pill-live" if (provider_info and provider_info.get("ready")) else ""

st.markdown(
    f"""
    <div class="cl-hero">
        <div class="cl-hero-row">
            <div class="cl-hero-mark">⚖️</div>
            <div>
                <h1>ContractLens</h1>
                <div class="cl-hero-tag">Reflection-loop AI for partner-quality contract review</div>
            </div>
        </div>
        <p>
            A typed LangGraph agent that drafts redlines, critiques them against a jurisdiction-specific
            7-point legal checklist, and iterates until the contract is partner-quality — or the cap is hit.
            Built for legal teams who'd rather review the result than the contract.
        </p>
        <div class="cl-pills">
            <span class="cl-pill {engine_state}">{engine_label}</span>
            <span class="cl-pill">Reflection Loop</span>
            <span class="cl-pill">{jurisdiction}</span>
            <span class="cl-pill">Cap · {max_iter} iter</span>
            <span class="cl-pill">Pydantic v2</span>
            <span class="cl-pill">LangGraph</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------
# Input
# --------------------------------------------------------------------------
st.markdown('<div class="cl-section-title">01 · Contract input</div>', unsafe_allow_html=True)
st.markdown('<div class="cl-section-h">Load a contract to analyse</div>', unsafe_allow_html=True)

input_tab, sample_tab = st.tabs(["Paste or upload", "Sample contracts"])

contract_text = ""
with input_tab:
    file = st.file_uploader("Upload a contract (.txt / .md)", type=["txt", "md"])
    if file:
        contract_text = file.read().decode("utf-8", errors="ignore")
        st.success(f"Loaded **{file.name}** — {len(contract_text):,} characters")
    pasted = st.text_area(
        "...or paste contract text here",
        height=180,
        placeholder="Paste a draft NDA, MSA, SaaS agreement, DPA, etc.",
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
                st.code(
                    sample_text[:3000] + ("\n…" if len(sample_text) > 3000 else ""),
                    language="text",
                )
            if st.button("Load this sample", key="load_sample"):
                contract_text = sample_text
                st.session_state["loaded_sample"] = sample_text
                st.rerun()
    if "loaded_sample" in st.session_state and not contract_text:
        contract_text = st.session_state["loaded_sample"]


# Run controls
col_run, col_clear, _ = st.columns([2, 1, 4])
with col_run:
    run_btn = st.button(
        "▶  Run reflection loop",
        type="primary",
        disabled=(not contract_text.strip() or st.session_state["is_running"]),
        use_container_width=True,
    )
with col_clear:
    if st.button("Clear results", use_container_width=True):
        st.session_state["result_state"] = None
        st.session_state["logs"] = []
        st.rerun()


# --------------------------------------------------------------------------
# Execute
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
    progress = st.progress(0.0, text="Initialising reflection loop...")
    status_box = st.empty()
    log_box = st.empty()
    logs = []

    expected_steps = 2 + max_iter * 2 + 1
    step = 0
    final_state_dict: dict | None = None

    try:
        for event in graph.stream(initial_state.model_dump(), stream_mode="updates"):
            for node_name, partial_update in event.items():
                step += 1
                logs.append(f"✓ `{node_name}` ran at {datetime.now().strftime('%H:%M:%S')}")
                progress.progress(min(step / expected_steps, 0.99),
                                  text=f"Running `{node_name}`...")
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
# Results
# --------------------------------------------------------------------------
result: GraphState | None = st.session_state.get("result_state")

if result is None:
    st.markdown(
        """
        <div class="cl-empty">
            <span class="cl-empty-tag">⚡ Ready</span>
            <h3>How the reflection loop works</h3>
            <div class="cl-flow-step">
                <div class="cl-flow-num">01</div>
                <div class="cl-flow-body">
                    <strong>Parser</strong>
                    <p>Splits the contract into clauses, classifies each into one of seven legal categories, and assigns a heuristic risk score from 0 to 10.</p>
                </div>
            </div>
            <div class="cl-flow-step">
                <div class="cl-flow-num">02</div>
                <div class="cl-flow-body">
                    <strong>Drafter</strong>
                    <p>Proposes redlines. On iteration ≥ 2, reads the previous critic's structured feedback so each cycle improves the draft instead of starting cold.</p>
                </div>
            </div>
            <div class="cl-flow-step">
                <div class="cl-flow-num">03</div>
                <div class="cl-flow-body">
                    <strong>Critic</strong>
                    <p>Evaluates the draft against the jurisdiction-specific seven-point checklist; produces a structured CriticVerdict with approved / issues / coverage.</p>
                </div>
            </div>
            <div class="cl-flow-step">
                <div class="cl-flow-num">04</div>
                <div class="cl-flow-body">
                    <strong>Decision gate</strong>
                    <p>Conditional edge — loops back to drafter if not approved AND iterations remain; otherwise exits to formatter.</p>
                </div>
            </div>
            <div class="cl-flow-step">
                <div class="cl-flow-num">05</div>
                <div class="cl-flow-body">
                    <strong>Formatter</strong>
                    <p>Produces the final marked-up contract with rationale per redline, an audit trail, and a coverage map.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()


# KPI strip
n_iter = result.iteration
n_redlines = len(result.redlines)
n_critical = sum(1 for i in result.critic_feedback if i.severity == Severity.CRITICAL)
n_high = sum(1 for i in result.critic_feedback if i.severity == Severity.HIGH)
duration = (datetime.now() - result.started_at).total_seconds()
diff_stats = count_changes(result.original_contract, result.current_draft)
total_issues_open = len(result.critic_feedback)
total_categories = len(result.enabled_categories)
covered = sum(1 for ok in (result.critic_verdict.coverage if result.critic_verdict else {}).values() if ok)

st.markdown('<div class="cl-section-title">02 · Run summary</div>', unsafe_allow_html=True)

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

st.markdown('<div class="cl-divider"></div>', unsafe_allow_html=True)


# Tabs
tab_loop, tab_clauses, tab_redlines, tab_diff, tab_final, tab_audit = st.tabs([
    "🔁  Reflection Loop",
    "📑  Clause Map",
    "✏️  Redlines",
    "📊  Diff View",
    "📋  Final Report",
    "🧾  Audit Log",
])


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
                f'<div class="cl-iter-row">'
                f'<span class="cl-iteration-pill">Iteration {rec.iteration}</span>'
                f'<span class="cl-badge {badge_cls}">{verdict_label}</span>'
                f'<span style="color: var(--cl-text-muted); font-size: 0.85rem; font-family: var(--cl-mono);">'
                f'{len(rec.redlines)} redlines · {len(v.issues) if v else 0} issues'
                f'</span></div>',
                unsafe_allow_html=True,
            )
            left, right = st.columns(2)
            with left:
                st.markdown(
                    '<div class="cl-panel"><h4>📝 Drafter strategy & redlines</h4>',
                    unsafe_allow_html=True,
                )
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
                            f'<div style="font-size: 0.88rem; color: var(--cl-text);">{r.rationale}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    if len(rec.redlines) > 8:
                        st.caption(f"… and {len(rec.redlines) - 8} more.")
                st.markdown("</div>", unsafe_allow_html=True)
            with right:
                st.markdown(
                    '<div class="cl-panel"><h4>🔍 Critic verdict & issues</h4>',
                    unsafe_allow_html=True,
                )
                if v:
                    st.markdown(
                        f"**Overall risk:** "
                        f'<span class="cl-tag cl-tag-{v.overall_risk.value}">{v.overall_risk.value}</span>',
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"_{v.summary}_")
                    if v.issues:
                        st.markdown("**Issues raised:**")
                        for issue in v.issues[:8]:
                            st.markdown(
                                f'<div class="cl-issue cl-issue-{issue.severity.value}">'
                                f'<div class="cl-issue-head">'
                                f'<span class="cl-tag cl-tag-{issue.severity.value}">{issue.severity.value}</span>'
                                f'<span class="cl-tag">{issue.category.value}</span>'
                                f'<span class="cl-tag">{issue.clause_id}</span></div>'
                                f'<div style="font-weight: 600; font-size: 0.9rem; color: var(--cl-text);">{issue.description}</div>'
                                f'<div style="font-size: 0.84rem; color: var(--cl-text-muted); margin-top: 6px;">'
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
                f'<span class="cl-tag" style="background:#{color}25; color:#{color}; border-color:#{color}50;">{label} · {c.risk_score:.1f}/10</span>'
                f'<span class="cl-tag">{c.id}</span>'
                f'<span class="cl-tag">{cat}</span></div>'
                f'<div style="font-weight: 600; color: var(--cl-text);">{c.heading}</div>'
                f'<div style="font-size: 0.84rem; color: var(--cl-text-muted); margin-top: 6px;">'
                f'{c.text[:300]}{"..." if len(c.text) > 300 else ""}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )


with tab_redlines:
    st.caption("All redlines accepted into the final draft, with rationale per change.")
    if not result.redlines:
        st.info("No redlines proposed.")
    else:
        by_cat: dict[str, list] = {}
        for r in result.redlines:
            by_cat.setdefault(r.category.value, []).append(r)
        for cat, rs in sorted(by_cat.items()):
            st.markdown(f"##### {cat.replace('_', ' ').title()} ({len(rs)} redlines)")
            for r in rs:
                with st.expander(f"[{r.severity.value}]  {r.clause_id}  ·  {r.change_type}"):
                    if r.original_text:
                        st.markdown("**Original**")
                        st.code(r.original_text, language="text")
                    if r.proposed_text:
                        st.markdown("**Proposed**")
                        st.code(r.proposed_text, language="text")
                    st.markdown("**Rationale**")
                    st.markdown(f"_{r.rationale}_")


with tab_diff:
    st.caption("Side-by-side diff between the original and the final marked-up contract.")
    diff_html = render_html_diff(result.original_contract, result.current_draft)
    st.components.v1.html(diff_html, height=700, scrolling=True)
    udiff = render_unified_diff(result.original_contract, result.current_draft)
    st.download_button(
        "⬇  Download unified diff (.patch)",
        data=udiff,
        file_name=f"contractlens_diff_{datetime.now().strftime('%Y%m%d_%H%M%S')}.patch",
        mime="text/x-patch",
    )


with tab_final:
    st.markdown(result.final_output)
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.download_button(
            "⬇  Download final report (.md)",
            data=result.final_output,
            file_name=f"contractlens_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_d2:
        st.download_button(
            "⬇  Download marked-up contract (.txt)",
            data=result.current_draft,
            file_name=f"contractlens_revised_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True,
        )


with tab_audit:
    st.caption("Every node invocation, in order, with timestamps. For Q&A and reproducibility.")
    if st.session_state["logs"]:
        for log in st.session_state["logs"]:
            st.markdown(f"- {log}")
    else:
        st.info("No logs from the most recent run (try re-running).")
    with st.expander("Raw GraphState (JSON)"):
        st.json(result.model_dump(mode="json"), expanded=False)
