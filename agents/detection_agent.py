"""
Detection Agent — "Is this fraud?"
Wraps your LightGBM + Graph + Geo fraud detection API.
"""
import aiohttp
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import FRAUD_API_URL, AGENT_TIMEOUT_SECONDS


class DetectionAgent:
    def __init__(self):
        self.name        = "DetectionAgent"
        self.api_url     = FRAUD_API_URL
        self.total_calls = 0
        self.fraud_found = 0

    async def check_transaction(self, amount=100.0, hour=12,
        card_id="unknown", merchant_id="unknown", ip="0.0.0.0",
        country="IN", city="unknown", v14=0.0, v4=0.0, v12=0.0,
        v10=0.0, v17=0.0, tx_count_1min=1, tx_count_10min=3,
        tx_count_60min=10, **kwargs) -> dict:
        """Check a single transaction for fraud."""
        self.total_calls += 1
        payload = {
            "Amount": amount, "hour": hour,
            "card_id": card_id, "merchant_id": merchant_id,
            "ip": ip, "country": country, "city": city,
            "V14": v14, "V4": v4, "V12": v12, "V10": v10, "V17": v17,
            "tx_count_1min": tx_count_1min,
            "tx_count_10min": tx_count_10min,
            "tx_count_60min": tx_count_60min,
        }
        for k, v in kwargs.items():
            if k.upper().startswith("V"):
                payload[k.upper()] = float(v)

        try:
            timeout = aiohttp.ClientTimeout(total=AGENT_TIMEOUT_SECONDS)
            async with aiohttp.ClientSession(timeout=timeout) as s:
                async with s.post(f"{self.api_url}/fraud/check", json=payload) as r:
                    if r.status == 429:
                        return {"decision": "RATE_LIMITED", "risk_score": 0.0,
                                "explanation": ["Rate limit exceeded"],
                                "graph_signals": [], "geo_signals": []}
                    result = await r.json()
                    if result.get("decision") in ["BLOCK", "STEP_UP_AUTH"]:
                        self.fraud_found += 1
                    return result
        except aiohttp.ClientConnectorError:
            return {"decision": "ERROR", "risk_score": 0.0,
                    "error": f"Cannot connect to {self.api_url}. Is fraud API running?",
                    "explanation": ["Start fraud API: uvicorn main:app --port 8000"],
                    "graph_signals": [], "geo_signals": []}
        except Exception as e:
            return {"decision": "ERROR", "risk_score": 0.0, "error": str(e),
                    "explanation": [str(e)], "graph_signals": [], "geo_signals": []}

    def get_stats(self) -> dict:
        return {"agent": self.name, "total_calls": self.total_calls,
                "fraud_found": self.fraud_found,
                "fraud_rate_pct": round(self.fraud_found/max(self.total_calls,1)*100, 2)}
