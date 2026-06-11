"""
Explanation Agent — "Explain this to a human"
Generates plain English fraud reports.
Uses Azure DeepSeek via Microsoft Foundry when available,
rule-based fallback otherwise.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import AZURE_OPENAI_API_KEY, AZURE_OPENAI_MODEL, USE_MOCK_GPT


class ExplanationAgent:
    def __init__(self):
        self.name = "ExplanationAgent"
        self.use_azure = not USE_MOCK_GPT
        self.total_explanations = 0

        if self.use_azure:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="https://fraudshield-deepseek-resource.services.ai.azure.com/openai/v1",
                    api_key=AZURE_OPENAI_API_KEY,
                )
                print("✅ Explanation Agent: Azure OpenAI connected")
            except Exception as e:
                print(f"⚠️  Azure OpenAI not available: {e}")
                self.use_azure = False

    def explain(self, investigation: dict, transaction: dict) -> dict:
        """Generate human-readable fraud explanation."""
        self.total_explanations += 1
        if self.use_azure:
            return self._explain_with_gpt(investigation, transaction)
        return self._explain_with_mock(investigation, transaction)

    def _explain_with_gpt(self, investigation: dict,
                           transaction: dict) -> dict:
        """Use Azure DeepSeek via Microsoft Foundry."""
        signals_text = "\n".join([
            f"- {s['type']}: {s.get('details', s.get('meaning', ''))}"
            for s in investigation.get("signals", [])
        ])

        prompt = (
            f"Fraud analyst report (3 short paragraphs, max 100 words):\n"
            f"Transaction: Rs{transaction.get('amount',0):.2f} | "
            f"{transaction.get('hour',0):02d}:00 | "
            f"{transaction.get('country','?')} | "
            f"Card: {str(transaction.get('card_id','?'))[:8]}\n"
            f"Decision: {investigation['decision']} | "
            f"Risk: {investigation['risk_score']:.0%} | "
            f"Pattern: {investigation['attack_pattern']}\n"
            f"Signals: {signals_text}\n"
            f"Write: 1) What happened 2) Why flagged 3) Actions needed"
        )

        try:
            response = self.client.chat.completions.create(
                model=AZURE_OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                timeout=8.0
            )
            explanation = response.choices[0].message.content
            return {
                "explanation": explanation,
                "source":      "azure_deepseek",
                "model":       AZURE_OPENAI_MODEL,
            }
        except Exception as e:
            print(f"⚠️  Azure error: {e}")
            return self._explain_with_mock(investigation, transaction)

    def _explain_with_mock(self, investigation: dict,
                            transaction: dict) -> dict:
        """Rule-based explanation (no Azure needed)."""
        decision   = investigation["decision"]
        risk_score = investigation["risk_score"]
        pattern    = investigation["attack_pattern"]
        signals    = investigation.get("signals", [])
        amount     = transaction.get("amount", 0)
        hour       = transaction.get("hour", 12)
        country    = transaction.get("country", "IN")
        card_id    = str(transaction.get("card_id", "unknown"))[:8]

        if decision == "BLOCK":
            p1 = (f"🚨 TRANSACTION BLOCKED — Risk Score: {risk_score:.0%}\n"
                  f"A Rs{amount:.2f} transaction on card {card_id}... at "
                  f"{hour:02d}:00 from {country} has been automatically blocked "
                  f"by FraudShield AI with {risk_score:.0%} confidence.")
        elif decision == "STEP_UP_AUTH":
            p1 = (f"⚠️  STEP-UP AUTHENTICATION REQUIRED — Risk Score: {risk_score:.0%}\n"
                  f"A Rs{amount:.2f} transaction on card {card_id}... requires "
                  f"additional verification. Risk level is elevated but not "
                  f"conclusive enough to block outright.")
        else:
            p1 = (f"✅ TRANSACTION APPROVED — Risk Score: {risk_score:.0%}\n"
                  f"A Rs{amount:.2f} transaction on card {card_id}... has been "
                  f"approved. No significant fraud signals detected.")

        reasons = []
        for sig in signals:
            stype = sig["type"]
            if stype == "ML_SIGNAL":
                reasons.append(
                    f"The bank's AI security model detected unusual "
                    f"transaction patterns (confidence: {sig['score']:.0%})")
            elif stype == "GRAPH_SIGNAL":
                reasons.append(
                    f"Graph analysis found coordinated suspicious activity — "
                    f"multiple cards sharing the same network connections")
            elif stype == "GEO_SIGNAL":
                reasons.append(
                    f"Geographic risk detected: transaction originated from "
                    f"{country} which has elevated fraud rates, "
                    f"possibly via VPN/proxy")
            elif stype == "TIME_SIGNAL":
                reasons.append(
                    f"Transaction occurred at {hour:02d}:00 — fraud peaks "
                    f"between 2-4am when cardholders are typically asleep")
            elif stype == "VELOCITY_SIGNAL":
                details = sig.get("details", [])
                if details:
                    reasons.append(details[0])

        p2 = "Why flagged:\n" + "\n".join(
            f"• {r}" for r in reasons) if reasons else \
             "No significant fraud signals detected."

        return {
            "explanation":    f"{p1}\n\n{p2}",
            "source":         "rule_based",
            "decision":       decision,
            "risk_score":     risk_score,
            "attack_pattern": pattern,
        }

    def get_stats(self) -> dict:
        return {
            "agent":              self.name,
            "total_explanations": self.total_explanations,
            "backend": "azure_deepseek" if self.use_azure else "rule_based"
        }
