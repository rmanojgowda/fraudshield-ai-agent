"""
Investigation Agent — "Why is this fraud?"
Analyzes SHAP values, geo signals, velocity patterns.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


class InvestigationAgent:
    def __init__(self):
        self.name = "InvestigationAgent"
        self.total_investigations = 0

    def investigate(self, detection_result: dict, transaction: dict) -> dict:
        """
        Deep dive into WHY a transaction was flagged.
        Extracts and interprets all fraud signals.
        """
        self.total_investigations += 1
        decision    = detection_result.get("decision", "UNKNOWN")
        risk_score  = detection_result.get("risk_score", 0.0)
        ml_score    = detection_result.get("ml_score", 0.0)
        graph_score = detection_result.get("graph_score", 0.0)
        geo_score   = detection_result.get("geo_score", 0.0)
        explanation = detection_result.get("explanation", [])
        graph_sigs  = detection_result.get("graph_signals", [])
        geo_sigs    = detection_result.get("geo_signals", [])

        # Classify risk level
        if risk_score >= 0.85:
            risk_level = "CRITICAL"
            risk_emoji = "🚨"
        elif risk_score >= 0.50:
            risk_level = "HIGH"
            risk_emoji = "⚠️"
        elif risk_score >= 0.25:
            risk_level = "MEDIUM"
            risk_emoji = "📊"
        else:
            risk_level = "LOW"
            risk_emoji = "✅"

        # Identify primary attack pattern
        attack_pattern = self._identify_attack_pattern(
            ml_score, graph_score, geo_score,
            graph_sigs, geo_sigs, transaction
        )

        # Build signal analysis
        signals = []

        # ML signals (SHAP)
        if ml_score > 0.5:
            signals.append({
                "type":     "ML_SIGNAL",
                "severity": "HIGH" if ml_score > 0.8 else "MEDIUM",
                "score":    round(ml_score, 4),
                "details":  explanation[:3] if explanation else [],
                "meaning":  "Bank's internal security features indicate fraud pattern"
            })

        # Graph signals
        if graph_score > 0.2:
            signals.append({
                "type":     "GRAPH_SIGNAL",
                "severity": "HIGH" if graph_score > 0.5 else "MEDIUM",
                "score":    round(graph_score, 4),
                "details":  graph_sigs,
                "meaning":  "Multiple cards/merchants sharing suspicious connections"
            })

        # Geo signals
        if geo_score > 0.1:
            signals.append({
                "type":     "GEO_SIGNAL",
                "severity": "HIGH" if geo_score > 0.5 else "MEDIUM",
                "score":    round(geo_score, 4),
                "details":  geo_sigs,
                "meaning":  "Geographic risk: country, travel pattern, or VPN detected"
            })

        # Time-based signal
        hour = transaction.get("hour", 12)
        if hour in [0, 1, 2, 3, 4]:
            signals.append({
                "type":     "TIME_SIGNAL",
                "severity": "MEDIUM",
                "score":    0.3,
                "details":  [f"Transaction at {hour:02d}:00 — peak fraud window (2-4am)"],
                "meaning":  "Fraud peaks between 2-4am when victims are asleep"
            })

        # Velocity signal
        tx_1min = transaction.get("tx_count_1min", 1)
        if tx_1min >= 4:
            signals.append({
                "type":     "VELOCITY_SIGNAL",
                "severity": "HIGH",
                "score":    min(tx_1min * 0.1, 0.8),
                "details":  [f"{tx_1min} transactions in last 1 minute (burst attack)"],
                "meaning":  "Card-testing attack: rapid low-value transactions"
            })

        # Amount signal
        amount = transaction.get("amount", 100)
        if amount > 1000:
            signals.append({
                "type":     "AMOUNT_SIGNAL",
                "severity": "MEDIUM",
                "score":    0.2,
                "details":  [f"High-value transaction: ₹{amount:.2f}"],
                "meaning":  "Large amounts are higher fraud risk"
            })

        # Recommended actions
        actions = self._recommend_actions(
            decision, risk_score, attack_pattern, transaction)

        return {
            "decision":        decision,
            "risk_level":      risk_level,
            "risk_emoji":      risk_emoji,
            "risk_score":      round(risk_score, 4),
            "attack_pattern":  attack_pattern,
            "signals":         signals,
            "signal_count":    len(signals),
            "primary_driver":  self._get_primary_driver(
                                    ml_score, graph_score, geo_score),
            "recommended_actions": actions,
            "scores": {
                "ml_score":    round(ml_score, 4),
                "graph_score": round(graph_score, 4),
                "geo_score":   round(geo_score, 4),
                "combined":    round(risk_score, 4),
            }
        }

    def _identify_attack_pattern(self, ml, graph, geo, graph_sigs,
                                   geo_sigs, tx):
        if graph > 0.5 and "ring" in str(graph_sigs).lower():
            return "COORDINATED_FRAUD_RING"
        if geo > 0.4 and "VPN" in str(geo_sigs):
            return "VPN_MASKED_ATTACK"
        if geo > 0.3 and ("RO" in str(geo_sigs) or "RU" in str(geo_sigs)):
            return "HIGH_RISK_COUNTRY"
        if geo > 0.4 and "IMPOSSIBLE" in str(geo_sigs):
            return "IMPOSSIBLE_TRAVEL"
        if tx.get("tx_count_1min", 0) >= 4:
            return "CARD_TESTING_BURST"
        if ml > 0.7:
            return "ML_FLAGGED_PATTERN"
        return "SUSPICIOUS_TRANSACTION"

    def _get_primary_driver(self, ml, graph, geo):
        scores = {"ML Model": ml, "Graph Detection": graph,
                  "Geographic Risk": geo}
        return max(scores, key=scores.get)

    def _recommend_actions(self, decision, risk_score,
                           pattern, tx):
        actions = []
        if decision == "BLOCK":
            actions.append("Block transaction immediately")
            actions.append("Notify cardholder via SMS/email")
        if pattern == "COORDINATED_FRAUD_RING":
            actions.append("Block all cards in the ring")
            actions.append("Flag merchant for review")
        if pattern == "VPN_MASKED_ATTACK":
            actions.append("Block IP range")
            actions.append("Require additional verification")
        if pattern == "IMPOSSIBLE_TRAVEL":
            actions.append("Freeze card immediately")
            actions.append("Contact cardholder to verify location")
        if risk_score > 0.9:
            actions.append("Escalate to fraud team immediately")
        actions.append("Log to audit trail")
        return actions

    def get_stats(self) -> dict:
        return {"agent": self.name,
                "total_investigations": self.total_investigations}
