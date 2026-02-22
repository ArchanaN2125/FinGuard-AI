class FinancialHealthEngine:
    def __init__(self):
        # Penalty weights
        self.WEIGHTS = {
            "avg_risk": 0.4,
            "high_risk_freq": 0.3,
            "trend": 0.2,
            "spending_deviation": 0.1
        }

    def calculate_health_score(self, user_profile, latest_analysis):
        """Calculates a financial health score from 0-100."""
        penalties = 0
        factors = []

        # 1. Average Risk Penalty (Last 5 avg)
        avg_risk = latest_analysis.get("last_5_avg_risk", 0)
        penalty1 = avg_risk * self.WEIGHTS["avg_risk"]
        penalties += penalty1
        if avg_risk > 30:
            factors.append(f"Average risk level ({avg_risk}) is elevated.")

        # 2. High Risk Frequency Penalty
        risk_history = user_profile.get("risk_history", [])
        high_risk_count = sum(1 for h in risk_history if h["score"] > 60)
        # Penalty increases with number of high risk events (max 100 for freq logic specifically)
        penalty2 = min(100, high_risk_count * 20) * self.WEIGHTS["high_risk_freq"]
        penalties += penalty2
        if high_risk_count > 0:
            factors.append(f"Detected {high_risk_count} high-risk transactions.")

        # 3. Trend Penalty
        trend = latest_analysis.get("risk_trend", "STABLE")
        penalty3 = 0
        if trend == "INCREASING":
            penalty3 = 50 * self.WEIGHTS["trend"]
            factors.append("Risk trend is increasing.")
        elif trend == "DECREASING":
            penalty3 = -20 * self.WEIGHTS["trend"] # Small bonus for decreasing risk
        penalties += penalty3

        # 4. Spending Deviation Penalty (from current txn)
        # We look at the statistical score from Layer 2 indirectly or simple check
        reasons = latest_analysis.get("reasons", [])
        deviation_penalty = 0
        for reason in reasons:
            if "deviates" in reason.lower():
                deviation_penalty = 50 * self.WEIGHTS["spending_deviation"]
                factors.append("Significant spending deviation detected.")
                break
        penalties += deviation_penalty

        # Final Score Calculation
        health_score = max(0, min(100, 100 - penalties))
        health_score = round(health_score, 2)

        # Status Mapping
        if health_score <= 40:
            status = "RISKY"
        elif health_score <= 70:
            status = "MODERATE"
        else:
            status = "HEALTHY"

        if not factors:
            factors.append("Consistent healthy financial behavior.")

        return {
            "health_score": health_score,
            "status": status,
            "factors": factors
        }
