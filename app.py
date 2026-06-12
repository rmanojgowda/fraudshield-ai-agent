"""
FraudShield AI — Streamlit Chat Interface
==========================================
Microsoft Agents League Hackathon 2026
"""

import streamlit as st
import asyncio
import json
import sys
import os
import re

sys.path.insert(0, os.path.dirname(__file__))
from orchestrator import FraudShieldOrchestrator

# ── Page Config ───────────────────────────────────────────────
st.set_page_config(
    page_title="FraudShield AI",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# ── Helper Functions (defined FIRST) ─────────────────────────

def _parse_transaction(text: str) -> dict:
    """Parse transaction from user message."""
    tx = {}
    try:
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
            return {k.lower(): v for k, v in parsed.items()}
    except Exception:
        pass

    patterns = {
        "amount":        r'amount[=:]\s*([\d.]+)',
        "hour":          r'hour[=:]\s*(\d+)',
        "card_id":       r'card[_-]?id[=:]\s*(\S+)',
        "country":       r'country[=:]\s*([A-Za-z]{2})',
        "v14":           r'v14[=:]\s*([-\d.]+)',
        "v12":           r'v12[=:]\s*([-\d.]+)',
        "v10":           r'v10[=:]\s*([-\d.]+)',
        "tx_count_1min": r'tx[_-]?(?:count[_-]?)?1min[=:]\s*(\d+)',
        "ip":            r'ip[=:]\s*([\d]+\.[\d]+\.[\d]+\.[\d]+)',
        "merchant_id":   r'merchant[_-]?id[=:]\s*(\S+)',
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text.lower())
        if match:
            val = match.group(1)
            if key in ["amount", "v14", "v12", "v10"]:
                tx[key] = float(val)
            elif key in ["hour", "tx_count_1min"]:
                tx[key] = int(val)
            else:
                # Uppercase country codes
                tx[key] = val.upper() if key == "country" else val
    return tx if tx else None


def _format_report(report: dict) -> str:
    if report.get("status") == "error":
        return (f"❌ **Error:** {report.get('message','Unknown error')}\n\n"
                f"💡 {report.get('hint','Make sure fraud API is running on port 8000')}")

    decision = report.get("decision", "UNKNOWN")
    risk     = report.get("risk_score", 0)
    pattern  = report.get("attack_pattern", "UNKNOWN")
    expl     = report.get("explanation", "No explanation available")
    scores   = report.get("scores", {})

    badge = {"BLOCK": "🚨 BLOCKED",
             "STEP_UP_AUTH": "⚠️ STEP-UP AUTH REQUIRED",
             "APPROVE": "✅ APPROVED",
             "RATE_LIMITED": "⏱️ RATE LIMITED"}.get(decision, decision)

    score_line = (f"ML: `{scores.get('ml_score',0):.3f}` | "
                  f"Graph: `{scores.get('graph_score',0):.3f}` | "
                  f"Geo: `{scores.get('geo_score',0):.3f}`")

    actions = report.get("actions", [])
    actions_text = "\n".join(f"• {a}" for a in actions[:4]) \
                   if actions else "No actions required"

    # Reasoning trail
    reasoning = report.get("reasoning_log", [])
    reasoning_text = ""
    if reasoning:
        reasoning_text = "\n\n**🧠 Agent Reasoning Trail:**\n" + \
            "\n".join(f"→ {r}" for r in reasoning)

    # Agents used
    agents = report.get("agents_used", [])
    agents_text = " → ".join(agents) if agents else "?"

    return (
        f"### {badge}\n"
        f"**Risk Score:** {risk:.0%} | **Pattern:** `{pattern}`\n\n"
        f"**Scores:** {score_line}\n\n"
        f"---\n\n"
        f"{expl}\n\n"
        f"---\n\n"
        f"{reasoning_text}\n\n"
        f"*Case: {report.get('case_id','?')} | "
        f"Latency: {report.get('latency_ms','?')}ms | "
        f"Agents: {agents_text}*"
    )


def _display_full_report(report: dict):
    """Display rich report in Streamlit."""
    if report.get("status") == "error":
        st.error(f"❌ {report.get('message')}")
        st.info(report.get("hint", ""))
        return

    decision = report.get("decision", "UNKNOWN")
    risk     = report.get("risk_score", 0)
    pattern  = report.get("attack_pattern", "")
    emoji    = report.get("risk_emoji", "")

    color = {"BLOCK": "#ff4444",
             "STEP_UP_AUTH": "#ff9900",
             "APPROVE": "#00aa44"}.get(decision, "#888888")

    st.markdown(
        f"<div style='background:{color};color:white;padding:14px;"
        f"border-radius:10px;font-size:18px;font-weight:bold;margin-bottom:12px'>"
        f"{emoji} {decision} — Risk: {risk:.0%}</div>",
        unsafe_allow_html=True
    )

    scores = report.get("scores", {})
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Combined Risk",  f"{risk:.3f}")
    c2.metric("ML Score",       f"{scores.get('ml_score',0):.3f}")
    c3.metric("Graph Score",    f"{scores.get('graph_score',0):.3f}")
    c4.metric("Geo Score",      f"{scores.get('geo_score',0):.3f}")

    st.markdown(f"**Attack Pattern:** `{pattern}`")

    signals = report.get("signals", [])
    if signals:
        st.markdown("**Fraud Signals Detected:**")
        for sig in signals:
            severity_color = {"HIGH": "🔴", "MEDIUM": "🟡",
                              "LOW": "🟢"}.get(sig.get("severity",""), "⚪")
            st.markdown(
                f"{severity_color} **{sig['type']}** "
                f"(score: {sig.get('score',0):.2f}) — {sig.get('meaning','')}"
            )

    st.markdown("**Investigation Report:**")
    st.info(report.get("explanation", "")[:1000])

    actions = report.get("actions", [])
    if actions:
        st.markdown("**Recommended Actions:**")
        for action in actions:
            st.markdown(f"• {action}")

    alert = report.get("alert", {})
    if alert.get("logged"):
        st.success(f"✅ Alert logged: {alert.get('alert_id','?')}")


def _handle_general_query(query: str, orch) -> str:
    q = query.lower()
    if any(w in q for w in ["stat", "how many", "count"]):
        stats = orch.get_system_stats()
        return (f"**📊 System Statistics:**\n"
                f"- Cases analyzed: {stats['orchestrator']['total_cases']}\n"
                f"- Fraud detected: {stats['detection']['fraud_found']}\n"
                f"- Fraud rate: {stats['detection']['fraud_rate_pct']:.1f}%\n"
                f"- Explanations generated: "
                f"{stats['explanation']['total_explanations']}\n"
                f"- Alerts sent: {stats['alert']['total_alerts']}")
    if any(w in q for w in ["help", "how", "what can"]):
        return ("**🛡️ FraudShield AI — How to Use:**\n\n"
                "**Option 1:** Type a transaction:\n"
                "`Check amount=500 hour=2 country=RO v14=-5.23`\n\n"
                "**Option 2:** Use Manual Check tab\n\n"
                "**Option 3:** Click Quick Test buttons in sidebar\n\n"
                "**I can detect:**\n"
                "• Card fraud (ML model, ROC-AUC 0.9883)\n"
                "• Fraud rings (graph detection)\n"
                "• VPN/proxy attacks (geo risk)\n"
                "• Card testing bursts (velocity)\n"
                "• Impossible travel patterns")
    return ("I'm **FraudShield AI** 🛡️\n\n"
            "I autonomously detect, investigate, and explain credit card fraud.\n\n"
            "Try: `Check amount=149.62 hour=2 country=RO v14=-5.23 tx_count_1min=5`\n\n"
            "Or click **🚨 Simulate Fraud Attack** in the sidebar!")


# ── Initialize Orchestrator ───────────────────────────────────
@st.cache_resource
def get_orchestrator():
    return FraudShieldOrchestrator()

orchestrator = get_orchestrator()

# ── Session State ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant",
         "content": ("👋 Welcome to **FraudShield AI**!\n\n"
                     "I'm an autonomous fraud detection agent. "
                     "I can detect fraud, investigate patterns, "
                     "and explain decisions in plain English.\n\n"
                     "Try clicking **🚨 Simulate Fraud Attack** "
                     "in the sidebar, or type a transaction to check!")}
    ]

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛡️ FraudShield AI")
    st.markdown("*Autonomous Fraud Detection Agent*")
    st.markdown("*Microsoft Agents League Hackathon 2026*")
    st.divider()

    st.markdown("**4 Specialized Agents:**")
    st.markdown("🔍 **Detection Agent** — LightGBM ML")
    st.markdown("🔬 **Investigation Agent** — Pattern Analysis")
    st.markdown("💬 **Explanation Agent** — Plain English")
    st.markdown("🔔 **Alert Agent** — Notify + Log")
    st.divider()

    stats = orchestrator.get_system_stats()
    col1, col2 = st.columns(2)
    col1.metric("Cases", stats["orchestrator"]["total_cases"])
    col2.metric("Fraud",  stats["detection"]["fraud_found"])
    st.divider()

    st.markdown("**Quick Tests:**")
    fraud_btn  = st.button("🚨 Simulate Fraud Attack",
                            use_container_width=True)
    normal_btn = st.button("✅ Normal Transaction",
                            use_container_width=True)
    ring_btn     = st.button("🕸️ Fraud Ring Attack",
                              use_container_width=True)
    darkweb_btn  = st.button("🌑 Dark Web Card",
                              use_container_width=True)
    testing_btn  = st.button("🔢 Card Testing Burst",
                              use_container_width=True)

    if fraud_btn:
        st.session_state["quick_tx"] = {
            "amount": 149.62, "hour": 2,
            "card_id": "card_attack_001",
            "country": "RO", "ip": "10.8.0.1",
            "v14": -5.23, "v12": -3.66, "tx_count_1min": 5
        }
    if normal_btn:
        st.session_state["quick_tx"] = {
            "amount": 85.0, "hour": 14,
            "card_id": "card_normal_001", "country": "IN"
        }
    if ring_btn:
        st.session_state["quick_tx"] = {
            "amount": 1.0, "hour": 3,
            "card_id": "card_ring_004",
            "merchant_id": "merchant_target",
            "ip": "10.0.0.1", "country": "IN",
            "tx_count_1min": 8, "v14": -4.5
        }
    
    if darkweb_btn:
        st.session_state["quick_tx"] = {
            "amount": 4999.99, "hour": 3,
            "card_id": "card_darkweb_001",
            "country": "RU", "ip": "10.55.0.1",
            "v14": -9.2, "v12": -5.1,
            "tx_count_1min": 1
        }
    if testing_btn:
        st.session_state["quick_tx"] = {
            "amount": 0.01, "hour": 4,
            "card_id": "card_test_burst",
            "country": "NG", "ip": "10.22.0.1",
            "v14": -3.5, "tx_count_1min": 12
        }

    st.divider()
    st.markdown("**Model Stats:**")
    st.markdown("ROC-AUC: `0.9883`")
    st.markdown("Precision: `93.44%`")
    st.markdown("Data: `284,807 txns`")
    st.markdown("Throughput: `100K RPM`")

# ── Main Header ───────────────────────────────────────────────
st.title("🛡️ FraudShield AI")
st.markdown(
    "**Autonomous Fraud Detection Agent System** | "
    "Microsoft Agents League Hackathon 2026 | "
    "LightGBM + Graph Detection + Azure OpenAI"
)

tab1, tab2, tab3 = st.tabs(
    ["💬 Agent Chat", "🔍 Manual Check", "📊 Dashboard"])

# ── Tab 1: Chat ───────────────────────────────────────────────
with tab1:
    # Show chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle sidebar quick buttons
    if "quick_tx" in st.session_state:
        tx     = st.session_state.pop("quick_tx")
        prompt = f"Check this transaction: {json.dumps(tx)}"

        st.session_state.messages.append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Running 4-agent investigation..."):
                report   = asyncio.run(orchestrator.investigate(tx))
            response = _format_report(report)
            st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response})
        st.rerun()

    # Chat input
    if prompt := st.chat_input(
            "Ask FraudShield AI... e.g. 'Check amount=500 hour=2 country=RO'"):
        st.session_state.messages.append(
            {"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("🤖 Agents working..."):
                tx = _parse_transaction(prompt)
                if tx:
                    report   = asyncio.run(orchestrator.investigate(tx))
                    response = _format_report(report)
                else:
                    response = _handle_general_query(prompt, orchestrator)
            st.markdown(response)

        st.session_state.messages.append(
            {"role": "assistant", "content": response})
        st.rerun()

# ── Tab 2: Manual Check ───────────────────────────────────────
with tab2:
    st.markdown("### 🔍 Manual Transaction Check")
    st.markdown("Fill in transaction details and run full investigation.")

    col1, col2 = st.columns(2)
    with col1:
        amount  = st.number_input("Amount (₹)", 0.01, 100000.0, 149.62)
        hour    = st.slider("Hour of Day", 0, 23, 2)
        card_id = st.text_input("Card ID", "card_test_001")
        country = st.selectbox("Country",
                    ["IN", "US", "RO", "RU", "GB", "NG", "DE",
                     "SG", "CN", "BR", "PK"])
    with col2:
        merchant   = st.text_input("Merchant ID", "merchant_X")
        ip         = st.text_input("IP Address", "10.8.0.1")
        tx_1min    = st.number_input("Tx in last 1 min", 1, 50, 5)
        v14        = st.slider("V14 (fraud signal)", -10.0, 5.0, -5.23,
                               help="More negative = higher fraud risk")

    st.markdown("---")
    if st.button("🔍 Run Full 4-Agent Investigation",
                 type="primary", use_container_width=True):
        tx = {
            "amount": amount, "hour": hour,
            "card_id": card_id, "merchant_id": merchant,
            "ip": ip, "country": country,
            "v14": v14, "tx_count_1min": tx_1min
        }
        with st.spinner("Running Detection → Investigation → "
                        "Explanation → Alert agents..."):
            report = asyncio.run(orchestrator.investigate(tx))
        _display_full_report(report)

# ── Tab 3: Dashboard ──────────────────────────────────────────
with tab3:
    st.markdown("### 📊 System Dashboard")

    stats = orchestrator.get_system_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Cases",
              stats["orchestrator"]["total_cases"])
    c2.metric("Fraud Detected",
              stats["detection"]["fraud_found"])
    c3.metric("Fraud Rate",
              f"{stats['detection']['fraud_rate_pct']:.1f}%")
    c4.metric("Alerts Sent",
              stats["alert"]["total_alerts"])

    st.divider()
    st.markdown("### Recent Alerts")
    alerts = orchestrator.alert.get_recent_alerts(limit=10)
    if alerts:
        for a in alerts:
            color = ("#ff4444" if a["decision"] == "BLOCK"
                     else "#ff9900" if a["decision"] == "STEP_UP_AUTH"
                     else "#00aa44")
            st.markdown(
                f"<div style='border-left:4px solid {color};"
                f"padding:10px 14px;margin:4px 0;"
                f"background:#f8f8f8;border-radius:4px'>"
                f"<b>{a['decision']}</b> | "
                f"₹{a['amount']:.2f} | "
                f"{a['country']} | "
                f"Risk: {a['risk_score']:.0%} | "
                f"<code>{a['attack_pattern']}</code> | "
                f"<small>{a['timestamp'][:19]}</small></div>",
                unsafe_allow_html=True
            )
    else:
        st.info("No alerts yet — run some transactions to see alerts here!")

    st.divider()
    st.markdown("### 🏆 About FraudShield AI")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Model Performance:**
| Metric | Value |
|--------|-------|
| ROC-AUC | 0.9883 |
| Precision | 93.44% |
| False Positives | 4/56,962 |
| Training Data | 284,807 txns |
        """)
    with col2:
        st.markdown("""
**System Scale:**
| Metric | Value |
|--------|-------|
| Peak RPM | 100,437 |
| GCP Projected | 3.5M RPM |
| P95 Latency | 13.4ms |
| Defense Layers | 4 |
        """)
    st.markdown("""
**4 Defense Layers:**
1. 🛡️ **Rate Limiter** — blocks card-testing attacks (<1ms)
2. 🤖 **LightGBM ML** — 39 features, ROC-AUC 0.9883
3. 🕸️ **Graph Detection** — fraud rings across workers (Redis-backed)
4. 🌍 **Geographic Risk** — country + VPN + impossible travel
    """)
# redeploy trigger v2
