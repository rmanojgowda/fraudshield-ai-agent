"""
FraudShield AI — Configuration
================================
Central config for all agents and services.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Fraud Detection API ───────────────────────────────────────
FRAUD_API_URL = os.getenv("FRAUD_API_URL", "demo")

# ── Azure OpenAI (add tomorrow after Azure signup) ────────────
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_KEY  = os.getenv("AZURE_OPENAI_API_KEY", "")
AZURE_OPENAI_MODEL    = os.getenv("AZURE_OPENAI_MODEL", "gpt-4o")

# ── Slack Alerts (optional) ───────────────────────────────────
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# ── Agent Settings ────────────────────────────────────────────
AGENT_TIMEOUT_SECONDS = 30
MAX_RETRIES           = 3

# ── Use mock GPT if Azure not configured ─────────────────────
USE_MOCK_GPT = not bool(AZURE_OPENAI_API_KEY)
