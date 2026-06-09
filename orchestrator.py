"""
FraudShield AI — Orchestrator
================================
Coordinates all 4 agents to provide complete
autonomous fraud investigation.

Flow:
  1. Detection Agent  → Is this fraud?
  2. Investigation Agent → Why is this fraud?
  3. Explanation Agent → Explain in plain English
  4. Alert Agent → Notify team + log audit trail
"""

import asyncio
import time
from agents.detection_agent    import DetectionAgent
from agents.investigation_agent import InvestigationAgent
from agents.explanation_agent  import ExplanationAgent
from agents.alert_agent        import AlertAgent


class FraudShieldOrchestrator:
    """
    Main orchestrator for FraudShield AI.
    Coordinates 4 specialized agents.
    """

    def __init__(self):
        self.detection     = DetectionAgent()
        self.investigation = InvestigationAgent()
        self.explanation   = ExplanationAgent()
        self.alert         = AlertAgent()
        self.total_cases   = 0

        print("🛡️  FraudShield AI Orchestrator initialized")
        print(f"   Detection:     {self.detection.name}")
        print(f"   Investigation: {self.investigation.name}")
        print(f"   Explanation:   {self.explanation.name}")
        print(f"   Alert:         {self.alert.name}")

    async def investigate(self, transaction: dict,
                          send_alert: bool = True) -> dict:
        """
        Full fraud investigation pipeline.
        
        Input: transaction dict with amount, hour, card_id, etc.
        Output: complete investigation report
        """
        self.total_cases += 1
        start = time.time()

        print(f"\n{'='*55}")
        print(f"🔍 FraudShield AI — Case #{self.total_cases}")
        print(f"   Card: {transaction.get('card_id','?')[:8]}... "
              f"Amount: ₹{transaction.get('amount',0):.2f} "
              f"Country: {transaction.get('country','IN')}")
        print(f"{'='*55}")

        # ── Step 1: Detection ─────────────────────────────────
        print("⚡ Step 1: Detection Agent running...")
        detection_result = await self.detection.check_transaction(
            **transaction)
        decision = detection_result.get("decision", "ERROR")
        print(f"   → Decision: {decision} "
              f"(score: {detection_result.get('risk_score',0):.3f})")

        if decision == "ERROR":
            return {
                "status":  "error",
                "message": detection_result.get("error", "Unknown error"),
                "hint":    "Make sure fraud API is running: uvicorn main:app --port 8000"
            }

        # ── Step 2: Investigation ─────────────────────────────
        print("🔬 Step 2: Investigation Agent analyzing...")
        investigation = self.investigation.investigate(
            detection_result, transaction)
        print(f"   → Pattern: {investigation['attack_pattern']} "
              f"| Signals: {investigation['signal_count']}")

        # ── Step 3: Explanation ───────────────────────────────
        print("💬 Step 3: Explanation Agent generating report...")
        explanation = self.explanation.explain(
            investigation, transaction)
        print(f"   → Source: {explanation.get('source','?')}")

        # ── Step 4: Alert ─────────────────────────────────────
        alert_result = {"logged": False}
        if send_alert and decision in ["BLOCK", "STEP_UP_AUTH"]:
            print("🔔 Step 4: Alert Agent notifying team...")
            alert_result = self.alert.send_alert(
                investigation, explanation, transaction)
            print(f"   → Alert ID: {alert_result.get('alert_id','?')} "
                  f"| Logged: {alert_result.get('logged',False)}")

        elapsed = round((time.time() - start) * 1000, 1)

        # ── Final Report ──────────────────────────────────────
        report = {
            "case_id":        f"FS-{self.total_cases:06d}",
            "status":         "complete",
            "decision":       decision,
            "risk_level":     investigation["risk_level"],
            "risk_emoji":     investigation["risk_emoji"],
            "risk_score":     detection_result.get("risk_score", 0),
            "attack_pattern": investigation["attack_pattern"],
            "transaction":    transaction,
            "scores": {
                "ml_score":    detection_result.get("ml_score", 0),
                "graph_score": detection_result.get("graph_score", 0),
                "geo_score":   detection_result.get("geo_score", 0),
                "combined":    detection_result.get("risk_score", 0),
            },
            "signals":        investigation["signals"],
            "explanation":    explanation["explanation"],
            "actions":        investigation["recommended_actions"],
            "alert":          alert_result,
            "latency_ms":     elapsed,
            "agents_used":    ["DetectionAgent", "InvestigationAgent",
                               "ExplanationAgent", "AlertAgent"],
        }

        print(f"\n✅ Investigation complete in {elapsed}ms")
        print(f"   {investigation['risk_emoji']} {decision} — "
              f"{investigation['risk_level']} RISK")
        return report

    async def quick_check(self, transaction: dict) -> dict:
        """Fast check — detection only, no full investigation."""
        return await self.detection.check_transaction(**transaction)

    def get_system_stats(self) -> dict:
        return {
            "orchestrator":  {"total_cases": self.total_cases},
            "detection":     self.detection.get_stats(),
            "investigation": self.investigation.get_stats(),
            "explanation":   self.explanation.get_stats(),
            "alert":         self.alert.get_stats(),
        }


# ── Quick test ────────────────────────────────────────────────
async def test():
    orchestrator = FraudShieldOrchestrator()

    # Test 1: High-risk fraud transaction
    print("\n" + "="*55)
    print("TEST 1: High-risk transaction (Romania + VPN + V14)")
    fraud_tx = {
        "amount":      149.62,
        "hour":        2,
        "card_id":     "card_suspect_001",
        "merchant_id": "merchant_X",
        "ip":          "10.8.0.1",
        "country":     "RO",
        "v14":         -5.23,
        "v12":         -3.66,
        "v10":         -3.09,
        "tx_count_1min": 5,
    }
    report = await orchestrator.investigate(fraud_tx)
    print(f"\nExplanation preview:")
    print(report["explanation"][:300])

    # Test 2: Normal transaction
    print("\n" + "="*55)
    print("TEST 2: Normal transaction (India, daytime)")
    normal_tx = {
        "amount":  50.0,
        "hour":    14,
        "card_id": "card_normal_001",
        "country": "IN",
    }
    report2 = await orchestrator.investigate(normal_tx, send_alert=False)
    print(f"Decision: {report2['decision']} | Risk: {report2['risk_score']:.3f}")

    print("\n" + "="*55)
    print("SYSTEM STATS:")
    import json
    print(json.dumps(orchestrator.get_system_stats(), indent=2))


if __name__ == "__main__":
    asyncio.run(test())
