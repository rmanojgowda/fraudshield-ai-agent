"""
Detection Agent — "Is this fraud?"
Wraps your LightGBM + Graph + Geo fraud detection API.
Falls back to demo mode for Streamlit Cloud deployment.
"""
import aiohttp
import random
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

        # ── Demo mode for Streamlit Cloud ─────────────────────
        if self.api_url == "demo":
            return self._demo_response(
                amount, hour, card_id, country,
                v14, tx_count_1min)

        # ── Live API mode ─────────────────────────────────────
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
                async with s.post(
                        f"{self.api_url}/fraud/check",
                        json=payload) as r:
                    if r.status == 429:
                        return {
                            "decision":      "RATE_LIMITED",
                            "risk_score":    0.0,
                            "explanation":   ["Rate limit exceeded"],
                            "graph_signals": [],
                            "geo_signals":   []
                        }
                    result = await r.json()
                    if result.get("decision") in ["BLOCK", "STEP_UP_AUTH"]:
                        self.fraud_found += 1
                    return result

        except aiohttp.ClientConnectorError:
            # API not running — fall back to demo mode
            return self._demo_response(
                amount, hour, card_id, country,
                v14, tx_count_1min)

        except Exception as e:
            return {
                "decision":      "ERROR",
                "risk_score":    0.0,
                "error":         str(e),
                "explanation":   [str(e)],
                "graph_signals": [],
                "geo_signals":   []
            }

    def _demo_response(self, amount, hour, card_id,
                       country, v14, tx_count_1min) -> dict:
        """
        Realistic demo responses without live API.
        Used on Streamlit Cloud and when API is unavailable.
        Uses same logic as real model but simplified.
        """
        # Calculate risk based on real fraud signals
        risk = 0.0
        if v14 < -3.0:                          risk += 0.40
        if v14 < -6.0:                          risk += 0.20
        if country in ["RO", "RU", "NG", "PK"]: risk += 0.30
        if hour < 5:                            risk += 0.10
        if tx_count_1min >= 4:                  risk += 0.20
        if tx_count_1min >= 8:                  risk += 0.15
        if amount > 1000:                       risk += 0.10

        ml_score    = min(
            round(risk * 0.8 + random.uniform(-0.03, 0.03), 4),
            0.99)
        graph_score = round(min(tx_count_1min * 0.08, 0.6), 4)
        geo_score   = (0.75 if country in ["RO", "RU", "NG"]
                       else 0.10)
        combined    = round(
            0.40 * ml_score +
            0.25 * graph_score +
            0.20 * geo_score,
            4)

        if combined >= 0.50:
            decision = "BLOCK"
        elif combined >= 0.25:
            decision = "STEP_UP_AUTH"
        else:
            decision = "APPROVE"

        if decision in ["BLOCK", "STEP_UP_AUTH"]:
            self.fraud_found += 1

        return {
            "request_id":    f"demo-{card_id[:6]}",
            "decision":      decision,
            "risk_score":    combined,
            "ml_score":      ml_score,
            "graph_score":   graph_score,
            "geo_score":     geo_score,
            "explanation":   [
                f"V14={v14:.2f} bank security signal",
                f"Country risk: {country}",
                f"Hour: {hour:02d}:00"
            ],
            "graph_signals": (
                [f"{tx_count_1min} rapid transactions detected"]
                if tx_count_1min >= 3 else []
            ),
            "geo_signals": (
                [f"High-risk country: {country}"]
                if geo_score > 0.3 else []
            ),
            "latency_ms":   12.5,
            "rate_limiter": "demo",
            "mode":         "demo"
        }

    def get_stats(self) -> dict:
        return {
            "agent":          self.name,
            "total_calls":    self.total_calls,
            "fraud_found":    self.fraud_found,
            "fraud_rate_pct": round(
                self.fraud_found / max(self.total_calls, 1) * 100, 2),
            "mode":           "demo" if self.api_url == "demo" else "live"
        }
