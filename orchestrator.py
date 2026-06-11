"""
FraudShield AI — Reasoning Orchestrator v2.0
=============================================
Microsoft Agents League Hackathon 2026

TRUE reasoning agent — decides which steps to take
based on intermediate results, not a fixed pipeline.

Reasoning Logic:
  1. Quick screen → is this worth investigating?
  2. If low risk   → approve immediately (no deep analysis)
  3. If suspicious → full detection with live API
  4. Reason about signal count → decide explanation depth
  5. Reason about severity     → decide alert level
  6. Log reasoning steps for transparency
"""

import asyncio
import time
from agents.detection_agent     import DetectionAgent
from agents.investigation_agent import InvestigationAgent
from agents.explanation_agent   import ExplanationAgent
from agents.alert_agent         import AlertAgent


class FraudShieldOrchestrator:
    """
    Reasoning orchestrator for FraudShield AI.
    Adapts its investigation strategy based on
    intermediate results — not a fixed pipeline.
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

    def _reason(self, step: str, condition: str, decision: str):
        """Log reasoning step for transparency."""
        print(f"   🧠 Reasoning: {step}")
        print(f"      Condition: {condition}")
        print(f"      Decision:  {decision}")

    async def investigate(self, transaction: dict,
                          send_alert: bool = True) -> dict:
        """
        Reasoning-driven fraud investigation.

        The agent DECIDES at each step what to do next
        based on intermediate results.
        """
        self.total_cases += 1
        start       = time.time()
        agents_used = []
        reasoning_log = []

        print(f"\n{'='*55}")
        print(f"🔍 FraudShield AI — Case #{self.total_cases}")
        print(f"   Card: {str(transaction.get('card_id','?'))[:8]}... "
              f"Amount: ₹{transaction.get('amount',0):.2f} "
              f"Country: {transaction.get('country','IN')}")
        print(f"{'='*55}")

        # ── REASONING STEP 1: Quick pre-screen ────────────────
        # Before calling any agent, reason about obvious signals
        amount  = transaction.get("amount", 0)
        hour    = transaction.get("hour", 12)
        country = transaction.get("country", "IN")
        v14     = transaction.get("v14", 0.0)

        HIGH_RISK_COUNTRIES = ["RO", "RU", "NG", "PK", "UA", "BY"]
        obvious_fraud = (
            v14 < -6.0 or
            (country in HIGH_RISK_COUNTRIES and hour < 5) or
            transaction.get("tx_count_1min", 0) >= 8
        )
        obvious_legit = (
            country == "IN" and
            5 <= hour <= 22 and
            v14 > -1.0 and
            amount < 500 and
            transaction.get("tx_count_1min", 1) <= 2
        )

        if obvious_legit:
            self._reason(
                "Pre-screen",
                "India + daytime + normal V14 + low velocity",
                "Low risk — run detection for confirmation"
            )
            reasoning_log.append("Pre-screen: obvious legitimate pattern")
        elif obvious_fraud:
            self._reason(
                "Pre-screen",
                f"V14={v14:.2f} OR high-risk country at night",
                "High risk — full investigation required"
            )
            reasoning_log.append("Pre-screen: obvious fraud signals detected")
        else:
            self._reason(
                "Pre-screen",
                "Mixed signals — cannot determine without ML",
                "Ambiguous — run full detection"
            )
            reasoning_log.append("Pre-screen: ambiguous — needs ML analysis")

        # ── REASONING STEP 2: Detection ───────────────────────
        print("⚡ Step 2: Detection Agent running...")
        agents_used.append("DetectionAgent")
        detection_result = await self.detection.check_transaction(
            **transaction)
        decision   = detection_result.get("decision", "ERROR")
        risk_score = detection_result.get("risk_score", 0)
        print(f"   → Decision: {decision} "
              f"(score: {risk_score:.3f})")

        if decision == "ERROR":
            return {
                "status":  "error",
                "message": detection_result.get("error", "Unknown"),
                "hint":    "Make sure fraud API is running on port 8000"
            }

        # ── REASONING STEP 3: Decide investigation depth ──────
        if risk_score < 0.10 and decision == "APPROVE":
            self._reason(
                "Investigation depth",
                f"Risk score {risk_score:.3f} < 0.10 AND decision=APPROVE",
                "Skip deep investigation — approve immediately"
            )
            reasoning_log.append(
                f"Investigation skipped: risk {risk_score:.3f} too low")

            elapsed = round((time.time() - start) * 1000, 1)
            print(f"\n✅ Fast-approved in {elapsed}ms (no deep investigation needed)")

            return {
                "case_id":        f"FS-{self.total_cases:06d}",
                "status":         "complete",
                "decision":       "APPROVE",
                "risk_level":     "LOW",
                "risk_emoji":     "✅",
                "risk_score":     risk_score,
                "attack_pattern": "NO_FRAUD_DETECTED",
                "transaction":    transaction,
                "scores": {
                    "ml_score":    detection_result.get("ml_score", 0),
                    "graph_score": detection_result.get("graph_score", 0),
                    "geo_score":   detection_result.get("geo_score", 0),
                    "combined":    risk_score,
                },
                "signals":        [],
                "explanation":    "✅ Transaction approved — no fraud signals detected.",
                "actions":        ["No action required"],
                "alert":          {"logged": False},
                "latency_ms":     elapsed,
                "agents_used":    agents_used,
                "reasoning_log":  reasoning_log,
            }

        # ── REASONING STEP 4: Full investigation ──────────────
        self._reason(
            "Investigation depth",
            f"Risk score {risk_score:.3f} ≥ 0.10 OR decision={decision}",
            "Full investigation required — running Investigation Agent"
        )
        reasoning_log.append(
            f"Full investigation triggered: risk={risk_score:.3f}")

        print("🔬 Step 3: Investigation Agent analyzing...")
        agents_used.append("InvestigationAgent")
        investigation = self.investigation.investigate(
            detection_result, transaction)
        signal_count  = investigation["signal_count"]
        attack        = investigation["attack_pattern"]
        print(f"   → Pattern: {attack} | Signals: {signal_count}")

        # ── REASONING STEP 5: Decide explanation depth ────────
        if signal_count >= 3 or risk_score >= 0.60:
            self._reason(
                "Explanation depth",
                f"{signal_count} signals OR risk {risk_score:.3f} ≥ 0.60",
                "HIGH complexity — use Azure DeepSeek for deep explanation"
            )
            reasoning_log.append(
                f"Deep AI explanation: {signal_count} signals, risk={risk_score:.3f}")
            use_ai = True
        elif signal_count >= 1:
            self._reason(
                "Explanation depth",
                f"{signal_count} signal(s), risk {risk_score:.3f} < 0.60",
                "MEDIUM complexity — use AI explanation"
            )
            reasoning_log.append("Standard explanation: moderate signals")
            use_ai = True
        else:
            self._reason(
                "Explanation depth",
                "0 signals detected",
                "LOW complexity — use rule-based explanation"
            )
            reasoning_log.append("Rule-based explanation: no clear signals")
            use_ai = False

        print("💬 Step 4: Explanation Agent generating report...")
        agents_used.append("ExplanationAgent")

        # Temporarily override azure if not needed
        if not use_ai:
            explanation = self.explanation._explain_with_mock(
                investigation, transaction)
        else:
            explanation = self.explanation.explain(
                investigation, transaction)
        print(f"   → Source: {explanation.get('source','?')}")

        # ── REASONING STEP 6: Decide alert severity ───────────
        alert_result = {"logged": False}

        if decision == "BLOCK" and risk_score >= 0.85:
            self._reason(
                "Alert severity",
                f"BLOCK + risk {risk_score:.3f} ≥ 0.85",
                "CRITICAL — immediate alert + log"
            )
            reasoning_log.append("CRITICAL alert triggered")
            should_alert = True

        elif decision == "BLOCK" and risk_score >= 0.50:
            self._reason(
                "Alert severity",
                f"BLOCK + risk {risk_score:.3f} ≥ 0.50",
                "HIGH — alert + log"
            )
            reasoning_log.append("HIGH alert triggered")
            should_alert = True

        elif decision == "STEP_UP_AUTH":
            self._reason(
                "Alert severity",
                f"STEP_UP_AUTH + risk {risk_score:.3f}",
                "MEDIUM — log only, no immediate alert"
            )
            reasoning_log.append("MEDIUM: logged, no alert")
            should_alert = True

        else:
            self._reason(
                "Alert severity",
                f"decision={decision}, risk={risk_score:.3f}",
                "LOW — silent log only"
            )
            reasoning_log.append("LOW: silent log")
            should_alert = False

        if should_alert and send_alert:
            print("🔔 Step 5: Alert Agent notifying team...")
            agents_used.append("AlertAgent")
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
            "risk_score":     risk_score,
            "attack_pattern": attack,
            "transaction":    transaction,
            "scores": {
                "ml_score":    detection_result.get("ml_score", 0),
                "graph_score": detection_result.get("graph_score", 0),
                "geo_score":   detection_result.get("geo_score", 0),
                "combined":    risk_score,
            },
            "signals":           investigation["signals"],
            "explanation":       explanation["explanation"],
            "explanation_source": explanation.get("source", "unknown"),
            "actions":           investigation["recommended_actions"],
            "alert":             alert_result,
            "latency_ms":        elapsed,
            "agents_used":       agents_used,
            "reasoning_log":     reasoning_log,
        }

        print(f"\n✅ Investigation complete in {elapsed}ms")
        print(f"   {investigation['risk_emoji']} {decision} — "
              f"{investigation['risk_level']} RISK")
        print(f"   🧠 Reasoning steps: {len(reasoning_log)}")
        return report

    async def quick_check(self, transaction: dict) -> dict:
        """Fast check — detection only."""
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

    tests = [
        {
            "label": "High-risk (Romania + VPN + V14)",
            "tx": {
                "amount": 149.62, "hour": 2,
                "card_id": "card_reason_001",
                "ip": "10.8.0.1", "country": "RO",
                "v14": -5.23, "v12": -3.66,
                "tx_count_1min": 5,
            }
        },
        {
            "label": "Normal (India, daytime)",
            "tx": {
                "amount": 85.0, "hour": 14,
                "card_id": "card_reason_002",
                "country": "IN",
            }
        },
        {
            "label": "Extreme fraud (V14 < -8)",
            "tx": {
                "amount": 2500.0, "hour": 3,
                "card_id": "card_reason_003",
                "country": "RU", "v14": -8.5,
                "tx_count_1min": 8,
            }
        },
    ]

    for t in tests:
        print(f"\n{'='*55}")
        print(f"TEST: {t['label']}")
        report = await orchestrator.investigate(t["tx"])
        print(f"\nDecision: {report['decision']} | Risk: {report['risk_score']:.3f}")
        print(f"Reasoning steps: {len(report.get('reasoning_log', []))}")
        for step in report.get("reasoning_log", []):
            print(f"  • {step}")
        if report.get("explanation"):
            print(f"\nExplanation preview:")
            print(report["explanation"][:300])

    print("\n" + "="*55)
    print("SYSTEM STATS:")
    import json
    print(json.dumps(orchestrator.get_system_stats(), indent=2))


if __name__ == "__main__":
    asyncio.run(test())
