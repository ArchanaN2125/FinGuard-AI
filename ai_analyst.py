class ContextBuilder:
    """Aggregates all relevant transaction and user data into a single context object."""
    @staticmethod
    def build_context(transaction, profile, fraud_analysis, health_analysis):
        return {
            "recent_transactions": profile.get("risk_history", [])[-5:],
            "average_spending": profile.get("average_spending", 0),
            "risk_trend": fraud_analysis.get("risk_trend", "Stable"),
            "health_score": health_analysis.get("health_score", 100),
            "triggered_rules": fraud_analysis.get("reasons", []),
            "current_transaction": transaction
        }

class RiskAnalystAI:
    """Simulates a Financial Risk Analyst AI to explain flagged transactions."""
    def __init__(self):
        self.persona = "Financial Risk Analyst AI"

    def generate_explanation(self, context):
        """Generates a professional, concise, simple English explanation."""
        rules = context["triggered_rules"]
        if not rules:
            return "Transaction alignments with established behavioral patterns. Low risk profile."

        txn = context["current_transaction"]
        avg = context["average_spending"]
        trend = context["risk_trend"]
        
        # Calculate precise multiplier for amount deviation
        multiplier_str = ""
        if avg > 0:
            multiplier = round(txn["amount"] / avg, 1)
            multiplier_str = f"This amount is {multiplier} times higher than the user's normal average of ${avg}. "
        
        # Professional narrative (3-4 lines)
        explanation = f"As your {self.persona}, I have flagged this transaction. "
        if "amount" in multiplier_str.lower():
            explanation += multiplier_str
        
        if any("location" in r.lower() for r in rules):
            explanation += f"It originated from an unrecognized location ({txn['location']}). "
            
        explanation += f"Given the '{trend}' risk trend, we recommend verification to ensure account security."
        
        return explanation
