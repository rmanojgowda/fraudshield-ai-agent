# 🛡️ FraudShield AI — Autonomous Fraud Detection Agent

[![Hackathon](https://img.shields.io/badge/Microsoft-Agents%20League%20Hackathon%202026-blue)](https://aiskillsnavigator.microsoft.com)
[![Track](https://img.shields.io/badge/Track-Reasoning%20Agents-orange)](https://aiskillsnavigator.microsoft.com)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Streamlit-red)](https://ai-fraud-de-kqninmrvd7glvcfzwzbh2l.streamlit.app/)
[![Python](https://img.shields.io/badge/Python-3.10-blue)](https://python.org)
[![ROC-AUC](https://img.shields.io/badge/ROC--AUC-0.9883-brightgreen)](https://github.com/rmanojgowda/fraudshield-ai-agent)

> **An autonomous AI agent system that detects, investigates, explains, and alerts on credit card fraud — without human intervention.**

👉 **[Try Live Demo](https://ai-fraud-de-kqninmrvd7glvcfzwzbh2l.streamlit.app/)**

---

## 🎯 The Problem

Banks process millions of transactions per day. Traditional fraud systems:
- ✅ Detect fraud
- ✅ Block the transaction
- ❌ Explain **why** it was blocked
- ❌ Investigate the attack pattern
- ❌ Automatically alert the fraud team

A fraud analyst still has to manually investigate every blocked transaction — reading raw ML scores, cross-referencing signals, writing reports, and notifying teams.

**FraudShield AI eliminates all manual steps using 4 specialized AI agents.**

---

## 💡 The Solution — 4 Autonomous Agents

```
Transaction arrives
       ↓
┌─────────────────────────────────────────────────────┐
│           FRAUDSHIELD AI ORCHESTRATOR               │
│                                                     │
│  Agent 1         Agent 2          Agent 3           │
│  Detection  →  Investigation  →  Explanation        │
│  LightGBM       SHAP + Geo +      Azure             │
│  Graph rings    Velocity          GPT-4o            │
│  Rate limit     Pattern ID        Plain English     │
│                      ↓                              │
│               Agent 4: Alert                        │
│               Slack + Audit Log                     │
└─────────────────────────────────────────────────────┘
       ↓
Complete fraud investigation report
Zero human effort required
```

---

## 🤖 The 4 Agents

### 🔍 Agent 1 — Detection Agent
**"Is this fraud?"**
- LightGBM ML model (ROC-AUC 0.9883, trained on 284,807 real transactions)
- Redis-backed graph ring detection (shared across all workers)
- Geographic risk scoring (country + VPN + impossible travel)
- Triple-layer rate limiting (5/10s + 100/hr + 3/hr/card)
- Returns: `APPROVE / STEP_UP_AUTH / BLOCK`

### 🔬 Agent 2 — Investigation Agent
**"Why is this fraud?"**
- Analyzes SHAP feature contributions from ML model
- Identifies attack pattern: `COORDINATED_FRAUD_RING`, `VPN_MASKED_ATTACK`, `CARD_TESTING_BURST`, `IMPOSSIBLE_TRAVEL`, `HIGH_RISK_COUNTRY`
- Calculates signal severity (HIGH / MEDIUM / LOW)
- Determines primary driver (ML vs Graph vs Geo)
- Recommends specific actions per attack pattern

### 💬 Agent 3 — Explanation Agent *(Azure OpenAI GPT-4o)*
**"Explain this to a human"**
- Takes raw fraud signals from Investigation Agent
- Generates plain English report using Azure OpenAI GPT-4o
- Written for fraud analysts, not engineers
- Falls back to rule-based explanation if Azure unavailable

### 🔔 Agent 4 — Alert Agent
**"Notify the right people"**
- Sends structured Slack alerts for high-risk blocks
- Logs complete audit trail to JSONL
- Includes all signals, scores, and recommended actions
- Rate-limited to prevent alert fatigue

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│              Streamlit Chat Interface                │
│  💬 Agent Chat  |  🔍 Manual Check  |  📊 Dashboard │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│           FraudShield Orchestrator                  │
│         Coordinates 4 specialized agents            │
└──┬──────────────┬─────────────┬──────────────┬──────┘
   ↓              ↓             ↓              ↓
Detection    Investigation  Explanation     Alert
Agent        Agent          Agent           Agent
   │              │             │              │
FastAPI       SHAP values   Azure OpenAI   Slack +
LightGBM      Geo signals   GPT-4o         JSONL log
Graph rings   Velocity
Rate limit    Pattern ID
   │
Redis ← shared across all 8 workers
```

---

## 📊 Real Performance Metrics

| Metric | Value |
|--------|-------|
| ML Model | LightGBM |
| ROC-AUC | **0.9883** |
| Precision | **93.44%** |
| False Positives | 4 per 56,962 transactions |
| Training Data | **284,807** real bank transactions |
| Peak Throughput | **100,437 RPM** (single machine) |
| Cloud Projected | **3,543,148 RPM** (100 GCP instances) |
| P95 Latency | **13.4ms** (async endpoint) |
| Defense Layers | 4 (Rate limit + ML + Graph + Geo) |
| Investigation Time | ~50ms end-to-end |

---

## 💬 Example Agent Conversation

```
User: Check this transaction

Transaction: ₹149.62 | 2:17 AM | Romania | VPN | V14=-5.23

──────────────────────────────────────────────────────
FraudShield AI:

🚨 BLOCKED — Risk Score: 87%
Pattern: VPN_MASKED_ATTACK

Signals detected:
🔴 ML_SIGNAL      (0.80) — Unusual bank security pattern
🔴 GEO_SIGNAL     (0.75) — Romania + VPN detected
🟡 TIME_SIGNAL    (0.30) — 2am peak fraud window
🔴 VELOCITY       (0.50) — 5 transactions in 1 minute

[GPT-4o Explanation]
This transaction exhibits three independent fraud
indicators. The V14 bank security feature at -5.23
is 6 standard deviations below normal, appearing in
94% of confirmed fraud cases. The transaction routes
through a Romanian VPN exit node — common in Eastern
European card-testing operations. Combined with 5
rapid transactions at 2:17 AM, this matches the
burst-and-test attack pattern preceding large fraud.

Recommended Actions:
• Block transaction immediately
• Notify cardholder via SMS/email
• Block IP range 10.8.0.0/24
• Flag merchant for review

✅ Alert logged: FSA-1781001128519
──────────────────────────────────────────────────────
```

---

## 🚀 Quick Start

```bash
# Clone
git clone https://github.com/rmanojgowda/fraudshield-ai-agent.git
cd fraudshield-ai-agent

# Setup
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt

# Configure (optional — works in demo mode without)
cp .env.example .env
# Add Azure OpenAI keys for GPT-4o explanation

# Run
streamlit run app.py
```

Open **http://localhost:8501** 🎉

---

## ⚙️ Environment Variables

```bash
FRAUD_API_URL=http://127.0.0.1:8000        # Local fraud API (optional)
AZURE_OPENAI_ENDPOINT=https://...          # Azure AI Foundry endpoint
AZURE_OPENAI_API_KEY=your-key             # Azure OpenAI API key
AZURE_OPENAI_MODEL=gpt-4o                 # Model deployment name
SLACK_WEBHOOK_URL=https://hooks.slack...  # Optional Slack alerts
```

> **Note:** App works in demo mode without any environment variables.

---

## 📁 Project Structure

```
fraudshield-ai-agent/
├── agents/
│   ├── detection_agent.py       ← Agent 1: LightGBM + Graph + Geo
│   ├── investigation_agent.py   ← Agent 2: SHAP + Pattern Analysis
│   ├── explanation_agent.py     ← Agent 3: Azure OpenAI GPT-4o
│   └── alert_agent.py           ← Agent 4: Slack + Audit Log
├── orchestrator.py              ← Coordinates all 4 agents
├── app.py                       ← Streamlit chat interface
├── config.py                    ← Environment configuration
├── .env.example                 ← Environment template
└── requirements.txt
```

---

## 🏆 Why This Stands Out

| Most Hackathon Projects | FraudShield AI |
|------------------------|----------------|
| Single AI call | 4 specialized agents |
| Fake/mock data | 284,807 real transactions |
| No metrics | ROC-AUC 0.9883, 100K RPM |
| Prototype only | Production-grade system |
| No live demo | ✅ Live Streamlit URL |
| GPT guessing | Real ML + SHAP signals |

---

## 👤 Author

**Manoj Gowda B G**
B.E. Information Science & Engineering
Siddaganga Institute of Technology, Tumkur (2026)
GitHub: [@rmanojgowda](https://github.com/rmanojgowda)

*Built on 3 months of production fraud detection engineering.*

---

## 📄 License

MIT License
