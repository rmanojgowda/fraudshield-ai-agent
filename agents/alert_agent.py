"""
Alert Agent — "Tell the right people"
Sends alerts and logs audit trail.
"""
import json, time, os, sys
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import SLACK_WEBHOOK_URL

os.makedirs("logs", exist_ok=True)
ALERT_LOG = "logs/fraudshield_alerts.jsonl"


class AlertAgent:
    def __init__(self):
        self.name          = "AlertAgent"
        self.total_alerts  = 0
        self.slack_enabled = bool(SLACK_WEBHOOK_URL)

    def send_alert(self, investigation: dict,
                   explanation: dict, transaction: dict) -> dict:
        """Send alert and log to audit trail."""
        self.total_alerts += 1
        decision   = investigation["decision"]
        risk_score = investigation["risk_score"]
        pattern    = investigation["attack_pattern"]
        amount     = transaction.get("amount", 0)
        card_id    = transaction.get("card_id", "unknown")[:8]
        country    = transaction.get("country", "IN")

        # Determine severity level
        if risk_score >= 0.85:
            severity = "CRITICAL"
        elif risk_score >= 0.60:
            severity = "HIGH"
        elif risk_score >= 0.35:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        alert_record = {
            "timestamp":      datetime.utcnow().isoformat(),
            "severity":       severity,
            "alert_id":       f"FSA-{int(time.time()*1000)}",
            "decision":       decision,
            "risk_score":     risk_score,
            "attack_pattern": pattern,
            "amount":         amount,
            "card_id":        card_id + "...",
            "country":        country,
            "signals_count":  investigation.get("signal_count", 0),
            "actions":        investigation.get("recommended_actions", []),
            "explanation_preview": explanation.get("explanation", "")[:200],
        }

        # Always log to file
        self._log_to_file(alert_record)

        # Send Slack if configured
        slack_sent = False
        # Alert based on severity
        if self.slack_enabled:
            if severity in ["CRITICAL", "HIGH"] and decision == "BLOCK":
                slack_sent = self._send_slack(alert_record)
            elif severity == "MEDIUM" and decision == "STEP_UP_AUTH":
                slack_sent = self._send_slack(alert_record)

        return {
            "alert_id":    alert_record["alert_id"],
            "logged":      True,
            "slack_sent":  slack_sent,
            "log_file":    ALERT_LOG,
            "alert_record": alert_record,
        }

    def _log_to_file(self, record: dict) -> None:
        try:
            with open(ALERT_LOG, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception:
            pass

    def _send_slack(self, record: dict) -> bool:
        try:
            import urllib.request
            emoji = "🚨" if record["decision"] == "BLOCK" else "⚠️"
            msg = {
                "text": f"{emoji} FraudShield AI Alert",
                "blocks": [{
                    "type": "section",
                    "text": {"type": "mrkdwn",
                             "text": (f"*{emoji} {record['decision']}* "
                                      f"| Risk: {record['risk_score']:.0%} "
                                      f"| ₹{record['amount']:.2f} "
                                      f"| {record['country']} "
                                      f"| Pattern: {record['attack_pattern']}")}
                }]
            }
            data = json.dumps(msg).encode()
            req  = urllib.request.Request(
                SLACK_WEBHOOK_URL, data=data,
                headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5)
            return True
        except Exception:
            return False

    def get_recent_alerts(self, limit: int = 10) -> list:
        alerts = []
        try:
            if os.path.exists(ALERT_LOG):
                with open(ALERT_LOG) as f:
                    lines = f.readlines()
                for line in lines[-limit:]:
                    alerts.append(json.loads(line.strip()))
        except Exception:
            pass
        return list(reversed(alerts))

    def get_stats(self) -> dict:
        return {"agent": self.name, "total_alerts": self.total_alerts,
                "slack_enabled": self.slack_enabled, "log_file": ALERT_LOG}
