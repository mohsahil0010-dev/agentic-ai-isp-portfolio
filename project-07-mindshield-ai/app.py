"""Streamlit interface for MindShield AI."""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv
from pydantic import ValidationError

from scamshield.exporter import report_to_json, report_to_markdown
from scamshield.llm import answer_general_chat
from scamshield.models import RiskLevel, SourceType
from scamshield.workflow import analyze_message


st.set_page_config(page_title="MindShield AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

load_dotenv()


def load_streamlit_secrets() -> None:
    try:
        for key in ("GROQ_API_KEY", "MINDSHIELD_MODEL"):
            if not os.getenv(key) and key in st.secrets:
                os.environ[key] = str(st.secrets[key])
    except (FileNotFoundError, KeyError):
        pass


load_streamlit_secrets()

st.markdown(
    """
    <style>
    :root { --ink:#182235; --muted:#6c7585; --line:#e5e8ee; --paper:#ffffff; --soft:#f7f8fb; --violet:#6658e8; --cyan:#129aa8; --red:#dc3545; }
    .stApp { background:var(--paper); color:var(--ink); }
    [data-testid="stHeader"] { background:rgba(255,255,255,.92); }
    .block-container { max-width:980px; padding-top:1rem; padding-bottom:7rem; }
    [data-testid="stSidebar"] { background:#111827; min-width:248px!important; max-width:248px!important; }
    [data-testid="stSidebar"] * { color:#eef1f8; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.35rem .15rem; }
    [data-testid="stSidebar"] .stButton button { background:transparent; border-color:#39445a; color:#eef1f8; border-radius:9px; }
    [data-testid="stSidebar"] .stButton button:hover { border-color:#8d82f2; background:#1b2539; }
    .brand { display:flex; align-items:center; gap:.65rem; margin:.25rem 0 1.25rem; }
    .brand-mark { width:34px; height:34px; border-radius:10px; background:linear-gradient(135deg,#6658e8,#129aa8); display:grid; place-items:center; color:white; font-weight:900; }
    .brand-name { color:white; font-size:1.12rem; font-weight:800; }
    .brand-sub { color:#96a4bd; font-size:.66rem; letter-spacing:.08em; }
    .topbar { display:flex; align-items:center; gap:.55rem; color:#5f6879; font-size:.82rem; margin:.1rem 0 1.4rem; }
    .topbar-mark { width:25px; height:25px; border-radius:8px; display:grid; place-items:center; color:white; background:linear-gradient(135deg,#6658e8,#129aa8); font-size:.72rem; }
    .topbar b { color:#263044; font-size:.9rem; }
    .welcome { text-align:center; padding:4.2rem 1rem 2rem; }
    .welcome-icon { width:56px; height:56px; margin:0 auto 1rem; border-radius:18px; display:grid; place-items:center; color:white; background:linear-gradient(135deg,#6658e8,#129aa8); font-size:1.35rem; box-shadow:0 10px 30px rgba(92,83,215,.18); }
    .welcome h1 { color:#1b2538; font-size:2rem; margin:.2rem 0 .45rem; }
    .welcome p { color:var(--muted); max-width:570px; margin:0 auto; }
    div[data-testid="stButton"] button { border-radius:12px; min-height:46px; border-color:var(--line); background:#fff; color:#30394a; text-align:left; }
    div[data-testid="stButton"] button:hover { border-color:#8d82f2; color:#4d42c8; }
    [data-testid="stChatMessage"] { background:transparent; padding:.85rem 0; }
    [data-testid="stChatInput"] { border-color:#dfe3ea; border-radius:16px; box-shadow:0 7px 28px rgba(31,42,68,.08); }
    .section-title { margin-top:.2rem; }
    .card { background:white; border:1px solid var(--line); border-radius:14px; padding:1.05rem 1.15rem; }
    .metric { color:var(--ink); font-size:1.75rem; font-weight:850; }
    .metric-label { color:var(--muted); font-size:.74rem; font-weight:750; letter-spacing:.09em; text-transform:uppercase; }
    .risk-track { background:#edf0f5; height:18px; border-radius:999px; overflow:hidden; margin:.65rem 0; }
    .risk-fill { height:100%; border-radius:999px; }
    .risk-low { background:#24a773; } .risk-caution { background:#e0a11b; } .risk-high { background:#ed6a3d; } .risk-critical { background:#dc3545; }
    .action-immediate { border-left:5px solid #dc3545; } .action-next { border-left:5px solid #e0a11b; } .action-preventive { border-left:5px solid #13a9b8; }
    .small-note { color:var(--muted); font-size:.82rem; }
    .stTabs [data-baseweb="tab"] { background:white; border-radius:9px 9px 0 0; padding:.55rem .85rem; }
    footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

GENERAL_SUGGESTIONS = [
    ("Explain AI agents simply", "Explain how artificial intelligence agents work in simple words."),
    ("Create a Python study plan", "Create a professional one-week study plan for learning Python."),
    ("Write a professional email", "Write a polite email requesting an internship interview."),
    ("Calculate a percentage", "Calculate (12500 * 0.10) + 12500"),
]

SCAM_SAMPLES = [
    "Congratulations! You won Rs. 500,000. Pay a processing fee of Rs. 2,500 through Easypaisa and send your OTP immediately. Claim now at http://bit.ly/free-prize.",
    "Dear applicant, you have been selected for a remote data entry job with salary PKR 85,000 without interview. Pay the training fee today and contact me on WhatsApp.",
    "Your parcel delivery failed. Pay the small customs fee within 2 hours or it will be returned: http://account-update.click/parcel",
    "Reminder: Your university workshop begins Monday at 10 AM in Room 4. Please bring your student card. Contact the department office if you cannot attend.",
]


def render_sidebar() -> str:
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">◆</div><div><div class="brand-name">MindShield AI</div>'
            '<div class="brand-sub">THINK • ANALYZE • PROTECT</div></div></div>',
            unsafe_allow_html=True,
        )
        mode = st.radio("Workspace", ["Chat", "Scam Check"], label_visibility="collapsed")
        st.divider()
        ai_status = st.session_state.get("ai_status")
        if ai_status == "connected":
            st.caption("🟢 AI connected")
        elif ai_status == "error":
            st.caption("🟠 AI connection needs attention")
        elif os.getenv("GROQ_API_KEY", "").strip():
            st.caption("🟡 Groq key loaded")
        else:
            st.caption("⚪ Add Groq key for AI chat")
        if mode == "Chat" and st.button("Clear chat", width="stretch"):
            st.session_state.general_messages = []
            st.session_state.ai_status = None
            st.rerun()
        if mode == "Scam Check" and st.button("New check", width="stretch"):
            st.session_state.report = None
            st.session_state.scam_content = ""
            st.rerun()
        with st.expander("Privacy & help"):
            st.caption("Scam Check works without an API key.")
            st.caption("Never paste passwords, OTPs, PINs, CVVs, seed phrases, full card numbers, or unnecessary identity numbers.")
        return mode


def render_hero() -> None:
    st.markdown(
        """
        <div class="topbar"><span class="topbar-mark">◆</span><b>MindShield AI</b><span>General assistant and scam protection</span></div>
        """,
        unsafe_allow_html=True,
    )


def should_route_to_scam(text: str) -> bool:
    lowered = text.casefold()
    explicit = any(phrase in lowered for phrase in ("is this scam", "check this message", "analyze this message", "analyse this message", "check this link", "suspicious message"))
    combined = ("http://" in lowered or "https://" in lowered) and any(term in lowered for term in ("otp", "pay", "fee", "winner", "account", "urgent"))
    return explicit or combined


def general_chat_page() -> None:
    if not st.session_state.general_messages:
        st.markdown(
            """
            <div class="welcome"><div class="welcome-icon">◆</div><h1>How can I help you?</h1>
            <p>Ask a question, request writing or planning help, solve a calculation, or switch to Scam Check for suspicious content.</p></div>
            """,
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        selected = None
        for index, (label, suggestion) in enumerate(GENERAL_SUGGESTIONS):
            with cols[index % 2]:
                if st.button(label, key=f"general_{index}", width="stretch"):
                    selected = suggestion
    else:
        selected = None
        for message in st.session_state.general_messages:
            with st.chat_message(message["role"], avatar="🛡️" if message["role"] == "assistant" else None):
                st.markdown(message["content"])
                if message.get("meta"):
                    st.caption(message["meta"])

    typed = st.chat_input("Ask MindShield anything…", key="general_chat_input")
    prompt = typed or selected
    if not prompt:
        return
    with st.chat_message("user"):
        st.write(prompt)
    st.session_state.general_messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant", avatar="🛡️"):
        if should_route_to_scam(prompt):
            with st.spinner("Routing to the specialist scam-analysis agents…"):
                try:
                    report = analyze_message(prompt)
                    answer = (
                        f"I routed this to the ScamShield workflow. **{report.assessment.level.value}: "
                        f"{report.assessment.score}/100.** {report.assessment.verdict} Open Scam Check for the full evidence and actions."
                    )
                    st.session_state.report = report
                    meta = "Route: specialist scam analysis"
                except Exception as exc:
                    answer = "The specialist analysis could not finish. Please open Scam Check and try the original message again."
                    meta = f"Workflow error: {type(exc).__name__}"
        else:
            with st.spinner("Thinking…"):
                result = answer_general_chat(st.session_state.general_messages)
            answer = result.answer
            st.session_state.ai_status = "connected" if result.model else "error" if result.warning else st.session_state.get("ai_status")
            meta_bits = []
            if result.tool_used:
                meta_bits.append("Calculated locally")
            if result.warning:
                meta_bits.append("AI connection needs attention")
            meta = " · ".join(meta_bits)
        st.markdown(answer)
        if meta:
            st.caption(meta)
    st.session_state.general_messages.append({"role": "assistant", "content": answer, "meta": meta})


def risk_style(level: RiskLevel) -> str:
    return {
        RiskLevel.LOW: "risk-low",
        RiskLevel.CAUTION: "risk-caution",
        RiskLevel.HIGH: "risk-high",
        RiskLevel.CRITICAL: "risk-critical",
    }[level]


def render_verdict(report) -> None:
    assessment = report.assessment
    left, right = st.columns([1.05, 1.8])
    with left:
        st.markdown(
            f'<div class="card"><div class="metric-label">Observed risk</div><div class="metric">{assessment.score}/100</div>'
            f'<div class="risk-track"><div class="risk-fill {risk_style(assessment.level)}" style="width:{assessment.score}%"></div></div>'
            f'<b>{assessment.level.value}</b><div class="small-note">{assessment.confidence} evidence confidence</div></div>',
            unsafe_allow_html=True,
        )
    with right:
        st.markdown("#### Assessment")
        st.write(report.summary)
        st.info(assessment.verdict)
    st.markdown("#### Safest response")
    st.code(report.safe_reply, language=None, wrap_lines=True)


def render_evidence(report) -> None:
    if report.indicators:
        rows = [
            {"Indicator": item.category, "Severity": item.severity, "Weight": item.weight, "Message evidence": item.evidence, "Why it matters": item.explanation}
            for item in report.indicators
        ]
        st.dataframe(rows, hide_index=True, width="stretch")
    else:
        st.info("No strong rule-based message indicator was detected. This does not prove legitimacy.")
    st.markdown("#### Similar known patterns")
    if report.pattern_matches:
        for match in report.pattern_matches:
            with st.expander(f"{match.name} · {match.similarity:.0%} similarity"):
                st.write(match.explanation)
                st.caption("Matched signals: " + ", ".join(match.matched_signals))
    else:
        st.caption("No local pattern exceeded the retrieval threshold.")


def render_entities(report) -> None:
    if report.entities:
        st.dataframe(
            [{"Type": item.entity_type, "Value": item.value, "Concern": item.concern} for item in report.entities],
            hide_index=True,
            width="stretch",
        )
    else:
        st.info("No URL, email, phone, amount, payment service, or credential request was extracted.")
    for inspection in report.url_inspections:
        with st.expander(f"Link inspection · {inspection.hostname} · {inspection.risk_points} points"):
            st.code(inspection.url)
            for finding in inspection.findings:
                st.markdown(f"- {finding}")
    st.caption("Links are inspected as text only. MindShield does not open them or claim to have checked live reputation.")


def render_actions(report) -> None:
    for item in report.recommended_actions:
        css = {"Immediate": "action-immediate", "Next": "action-next", "Preventive": "action-preventive"}[item.priority]
        st.markdown(
            f'<div class="card {css}" style="margin-bottom:.7rem"><div class="metric-label">{item.priority}</div>'
            f'<b>{item.action}</b><div class="small-note" style="margin-top:.35rem">{item.reason}</div></div>',
            unsafe_allow_html=True,
        )
    st.markdown("#### Reporting guidance")
    for line in report.reporting_guidance:
        st.markdown(f"- {line}")


def render_knowledge(report) -> None:
    st.markdown("#### Retrieved safety knowledge")
    for item in report.retrieved_guidance:
        title = " ".join(item.split()[:6]) + "…"
        with st.expander(title):
            st.write(item)
    st.markdown("#### Important limitations")
    for item in report.limitations:
        st.markdown(f"- {item}")


def render_trace(report) -> None:
    st.caption("The trace shows which branch and evidence each specialist agent used.")
    for index, trace in enumerate(report.agent_trace, start=1):
        with st.expander(f"{index}. {trace.agent} · {trace.status}", expanded=index == len(report.agent_trace)):
            st.write(trace.decision)
            for evidence in trace.evidence:
                st.markdown(f"- {evidence}")


def render_report(report) -> None:
    st.divider()
    st.markdown("### Multi-agent analysis report")
    tabs = st.tabs(["Verdict", "Evidence", "Links & entities", "Safety actions", "Knowledge & limits", "Agent trace"])
    with tabs[0]: render_verdict(report)
    with tabs[1]: render_evidence(report)
    with tabs[2]: render_entities(report)
    with tabs[3]: render_actions(report)
    with tabs[4]: render_knowledge(report)
    with tabs[5]: render_trace(report)
    st.markdown("#### Download the evidence report")
    cols = st.columns([1, 1, 2])
    with cols[0]:
        st.download_button("Download Markdown", report_to_markdown(report), "mindshield-analysis.md", "text/markdown", width="stretch")
    with cols[1]:
        st.download_button("Download JSON", report_to_json(report), "mindshield-analysis.json", "application/json", width="stretch")


def scam_analyzer_page() -> None:
    st.markdown("## Check a suspicious message")
    st.caption("Paste the message, email, offer, or link. MindShield will explain the warning signs and safest next steps.")
    sample_cols = st.columns(3)
    labels = ["Prize message", "Fake job", "Parcel link"]
    for index, label in enumerate(labels):
        with sample_cols[index]:
            if st.button(label, key=f"scam_{index}", width="stretch"):
                st.session_state.scam_content = SCAM_SAMPLES[index]
    content = st.text_area(
        "Suspicious message, email, offer, or link",
        height=160,
        placeholder="Paste the suspicious content here…",
        key="scam_content",
    )
    with st.expander("Add details (optional)"):
        source_value = st.selectbox("Where did it arrive?", [item.value for item in SourceType])
        context = st.text_input("Context", placeholder="Example: I did not expect this job offer")
        cols = st.columns(3)
        with cols[0]: clicked = st.checkbox("Opened link")
        with cols[1]: sent_money = st.checkbox("Sent money")
        with cols[2]: shared = st.checkbox("Shared a code")
    if st.button("Check message", type="primary", width="stretch", disabled=len(content.strip()) < 15):
        try:
            with st.spinner("Inspecting entities, persuasion signals, patterns, risk, and safest actions…"):
                st.session_state.report = analyze_message(
                    content=content,
                    source_type=SourceType(source_value),
                    user_context=context,
                    clicked_link=clicked,
                    sent_money=sent_money,
                    shared_sensitive_info=shared,
                )
        except (ValidationError, ValueError) as exc:
            st.error(f"The case could not be validated: {exc}")
        except Exception as exc:
            st.error("The analysis could not finish. Please review the content and try again.")
            with st.expander("Technical details"):
                st.code(f"{type(exc).__name__}: {exc}")
    if st.session_state.report is not None:
        render_report(st.session_state.report)


def system_guide_page() -> None:
    st.markdown("### How MindShield works")
    st.markdown(
        """
        MindShield has two coordinated paths:

        1. **General AI Chat** sends ordinary questions to the configured Groq language model. A local calculator handles suitable arithmetic safely without an LLM.
        2. **Scam Analyzer** uses a conditional LangGraph workflow. It validates the case, extracts entities, inspects link structure, detects social-engineering signals, retrieves similar patterns and safety knowledge, scores the risk, then selects either an urgent-protection or balanced-verification branch.

        The scam workflow is deterministic and works without an API key. Groq is optional for improving the summary.
        """
    )
    st.markdown("#### Scam-analysis agent team")
    agents = [
        ("Intake & Intent", "Validates input and detects the source."),
        ("Entity & Link Inspector", "Extracts URLs, emails, phones, amounts, services, and credential requests."),
        ("Social Engineering Analyst", "Detects urgency, threats, secrecy, fees, prizes, and account-takeover requests."),
        ("Pattern Retrieval Agent", "Finds related scam patterns and safety guidance from the local knowledge base."),
        ("Evidence & Risk Scorer", "Combines transparent evidence into a bounded 0-100 score."),
        ("Conditional Response Agent", "Chooses urgent protection or balanced verification."),
        ("Lead Safety Coordinator", "Creates the validated report, actions, limitations, and exports."),
    ]
    for name, description in agents:
        st.markdown(f"**{name}:** {description}")


if "general_messages" not in st.session_state:
    st.session_state.general_messages = []
if "report" not in st.session_state:
    st.session_state.report = None
if "scam_content" not in st.session_state:
    st.session_state.scam_content = ""
if "ai_status" not in st.session_state:
    st.session_state.ai_status = None

mode = render_sidebar()
render_hero()
if mode == "Chat":
    general_chat_page()
else:
    scam_analyzer_page()
