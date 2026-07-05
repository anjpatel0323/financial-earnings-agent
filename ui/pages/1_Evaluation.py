"""
Evaluation Dashboard
--------------------
Shows RAGAS evaluation results in a visual dashboard.
"""

import json
import os
import glob
import streamlit as st

st.set_page_config(
    page_title="FEIA — Evaluation",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0a0e1a; color: #e2e8f0; }
[data-testid="stSidebar"] { background-color: #0d1117; border-right: 1px solid #1e2d40; }
.metric-card {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 8px;
    padding: 20px;
    text-align: center;
}
.metric-label { font-size: 11px; color: #4a7fa5; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }
.metric-score { font-size: 36px; font-weight: 700; font-family: monospace; margin-bottom: 4px; }
.metric-rating { font-size: 12px; font-weight: 600; letter-spacing: 0.1em; }
.score-excellent { color: #00d4aa; }
.score-good { color: #f0a500; }
.score-fair { color: #e07b00; }
.score-bad { color: #e74c3c; }
.bar-bg { background: #1e2d40; border-radius: 4px; height: 8px; margin-top: 8px; }
.bar-fill { height: 8px; border-radius: 4px; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div style="font-size:24px; font-weight:700; color:#00d4aa; font-family:monospace; margin-bottom:4px;">▸ RAG Evaluation Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div style="font-size:12px; color:#4a7fa5; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:1.5rem;">Powered by RAGAS · Measuring RAG pipeline quality</div>', unsafe_allow_html=True)

# ── Load latest results ───────────────────────────────────────────────────────
results_dir = "evaluate/results"
result_files = sorted(glob.glob(f"{results_dir}/eval_*.json"), reverse=True)

if not result_files:
    st.warning("No evaluation results found. Run: `python -m evaluate.ragas_eval`")
    st.stop()

with open(result_files[0]) as f:
    data = json.load(f)

metrics  = data["metrics"]
overall  = data["overall"]
ts       = data["timestamp"][:19].replace("T", " ")
n_tests  = data["num_tests"]

# ── Overall score banner ──────────────────────────────────────────────────────
overall_color = "#00d4aa" if overall >= 0.8 else "#f0a500" if overall >= 0.6 else "#e74c3c"
overall_label = "EXCELLENT" if overall >= 0.8 else "GOOD" if overall >= 0.6 else "NEEDS WORK"

st.markdown(f"""
<div style="background:#0d1117; border:1px solid #1e3a5f; border-radius:12px; padding:24px; margin-bottom:1.5rem; display:flex; align-items:center; justify-content:space-between;">
    <div>
        <div style="font-size:12px; color:#4a7fa5; text-transform:uppercase; letter-spacing:0.08em; margin-bottom:6px;">Overall RAG Quality Score</div>
        <div style="font-size:48px; font-weight:700; font-family:monospace; color:{overall_color};">{overall:.3f}</div>
        <div style="font-size:13px; color:{overall_color}; font-weight:600; letter-spacing:0.1em;">{overall_label}</div>
    </div>
    <div style="text-align:right;">
        <div style="font-size:12px; color:#2d4a6b;">Last evaluated</div>
        <div style="font-size:14px; color:#4a7fa5; font-family:monospace;">{ts}</div>
        <div style="font-size:12px; color:#2d4a6b; margin-top:8px;">Test cases</div>
        <div style="font-size:20px; color:#00d4aa; font-family:monospace; font-weight:600;">{n_tests}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── 4 metric cards ────────────────────────────────────────────────────────────
def score_class(s):
    if s >= 0.8: return "score-excellent", "EXCELLENT"
    if s >= 0.6: return "score-good",      "GOOD"
    if s >= 0.4: return "score-fair",      "FAIR"
    return "score-bad", "NEEDS WORK"

def bar_color(s):
    if s >= 0.8: return "#00d4aa"
    if s >= 0.6: return "#f0a500"
    return "#e74c3c"

metric_info = {
    "faithfulness":      ("Faithfulness",      "No hallucination — answer grounded in retrieved context"),
    "answer_relevancy":  ("Answer Relevancy",   "Answer directly addresses the question asked"),
    "context_precision": ("Context Precision",  "Retrieved chunks are relevant — no noise"),
    "context_recall":    ("Context Recall",     "All necessary information was retrieved"),
}

cols = st.columns(4)
for col, (key, (label, desc)) in zip(cols, metric_info.items()):
    score = metrics.get(key, 0)
    cls, rating = score_class(score)
    color = bar_color(score)
    pct   = int(score * 100)
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-score {cls}">{score:.3f}</div>
            <div class="metric-rating {cls}">{rating}</div>
            <div class="bar-bg">
                <div class="bar-fill" style="width:{pct}%; background:{color};"></div>
            </div>
            <div style="font-size:11px; color:#2d4a6b; margin-top:10px;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

# ── Per-question breakdown ────────────────────────────────────────────────────
st.markdown('<div style="margin-top:1.5rem; margin-bottom:1rem; font-size:15px; font-weight:500; color:#e2e8f0;">Per-question breakdown</div>', unsafe_allow_html=True)

per_q = data.get("per_question", [])
for i, row in enumerate(per_q, 1):
    q = row.get("question", "")
    f = row.get("faithfulness", 0)
    a = row.get("answer_relevancy", 0)
    cp = row.get("context_precision", 0)
    cr = row.get("context_recall", 0)
    avg = (f + a + cp + cr) / 4
    avg_color = bar_color(avg)

    with st.expander(f"Q{i}: {q[:80]}..."):
        c1, c2, c3, c4 = st.columns(4)
        for col, label, val in [
            (c1, "Faithfulness",      f),
            (c2, "Ans. Relevancy",    a),
            (c3, "Context Precision", cp),
            (c4, "Context Recall",    cr),
        ]:
            cls, _ = score_class(val)
            with col:
                st.markdown(f"""
                <div style="text-align:center; padding:12px; background:#0d1117; border-radius:6px; border:1px solid #1e2d40;">
                    <div style="font-size:10px; color:#4a7fa5; margin-bottom:4px;">{label}</div>
                    <div style="font-size:20px; font-weight:600; font-family:monospace;" class="{cls}">{val:.3f}</div>
                </div>
                """, unsafe_allow_html=True)

# ── Run eval button ───────────────────────────────────────────────────────────
st.markdown('<div style="margin-top:1.5rem"></div>', unsafe_allow_html=True)
st.divider()
st.markdown('<div style="font-size:13px; color:#4a7fa5; margin-bottom:8px;">Run a fresh evaluation to update scores</div>', unsafe_allow_html=True)
if st.button("Run evaluation now", type="primary"):
    with st.spinner("Running RAGAS evaluation — takes 2-3 minutes..."):
        import subprocess
        result = subprocess.run(
            ["python", "-m", "evaluate.ragas_eval"],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            st.success("Evaluation complete! Refresh the page to see new scores.")
        else:
            st.error(result.stderr[-500:])