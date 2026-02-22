import math
from datetime import datetime

class FraudDetectionEngine:
    def __init__(self):
        # Weights for the 3-layer hybrid score
        self.LAYER_WEIGHTS = {
            "rule_based": 0.4,
            "statistical": 0.3,
            "simulated_ml": 0.3
        }
        self.TIME_THRESHOLD_SECONDS = 60  # High frequency threshold

    def analyze_transaction(self, transaction, user_profile):
        """Processes a transaction through 3 layers and returns risk assessment."""
        
        # Layer 1: Rule-Based Logic
        layer1_score, layer1_reasons = self._layer1_rules(transaction, user_profile)
        
        # Layer 2: Statistical Anomaly
        layer2_score, layer2_reasons = self._layer2_statistical(transaction, user_profile)
        
        # Layer 3: Simulated ML Risk Score
        layer3_score = self._layer3_simulated_ml(layer1_score, layer2_score)
        
        # Combine Layers into final Score (0-100)
        final_score = (
            (layer1_score * self.LAYER_WEIGHTS["rule_based"]) +
            (layer2_score * self.LAYER_WEIGHTS["statistical"]) +
            (layer3_score * self.LAYER_WEIGHTS["simulated_ml"])
        )
        final_score = min(100, round(final_score, 2))
        
        # Classification
        risk_level = self._classify_risk(final_score)
        
        # Risk Trend Analysis
        risk_history = user_profile.get("risk_history", [])
        trend, last_avg = self._calculate_risk_trend(risk_history, final_score)
        
        # Combine all reasons
        all_reasons = list(set(layer1_reasons + layer2_reasons))
        if final_score > 60 and not all_reasons:
            all_reasons.append("High cumulative risk score across multiple layers.")

        # Extract Risk Categories
        risk_categories = []
        for reason in all_reasons:
            if "amount" in reason.lower(): risk_categories.append("High Amount")
            if "location" in reason.lower(): risk_categories.append("New Location")
            if "frequency" in reason.lower() or "seconds" in reason.lower(): risk_categories.append("High Frequency")
        
        if not risk_categories and final_score > 30:
            risk_categories.append("Behavioral Anomaly")

        return {
            "transaction_id": transaction["transaction_id"],
            "final_risk_score": final_score,
            "risk_level": risk_level,
            "risk_category": list(set(risk_categories)),
            "reasons": all_reasons,
            "risk_trend": trend,
            "last_5_avg_risk": last_avg,
            "risk_history": risk_history
        }

    def _calculate_risk_trend(self, risk_history, current_score):
        """Calculates risk trend (UPPERCASE) and average of last 5 transactions."""
        if not risk_history:
            return "STABLE", current_score

        # Get scores from history (up to last 5)
        scores = [h["score"] for h in risk_history[-5:]]
        avg_score = round(sum(scores) / len(scores), 2)

        # Detect trend
        if current_score > avg_score + 5:
            trend = "INCREASING"
        elif current_score < avg_score - 5:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        return trend, avg_score

    def _layer1_rules(self, txn, profile):
        """Layer 1: Rule-Based Logic."""
        score = 0
        reasons = []
        
        avg_amount = profile["average_spending"]
        
        # Rule 1: Amount > 3x average
        if profile["total_transactions"] > 2: # Only check if we have some history
            if txn["amount"] > (3 * avg_amount):
                score += 50
                reasons.append(f"Transaction amount ({txn['amount']}) is more than 3x the user average ({avg_amount}).")

        # Rule 2: New Location
        if txn["location"] not in profile["location_history"]:
            score += 30
            reasons.append(f"Transaction from a new location: {txn['location']}.")

        # Rule 3: High Frequency
        if profile["last_transaction_time"]:
            fmt = "%Y-%m-%d %H:%M:%S"
            try:
                t1 = datetime.strptime(profile["last_transaction_time"], fmt)
                t2 = datetime.strptime(txn["timestamp"], fmt)
                delta = (t2 - t1).total_seconds()
                
                if delta < self.TIME_THRESHOLD_SECONDS:
                    score += 40
                    reasons.append(f"High transaction frequency detected ({int(delta)}s since last txn).")
            except Exception:
                pass

        return min(100, score), reasons

    def _layer2_statistical(self, txn, profile):
        """Layer 2: Statistical Anomaly."""
        score = 0
        reasons = []
        
        if profile["total_transactions"] < 2:
            return 0, []

        avg_amount = profile["average_spending"]
        amount = txn["amount"]
        
        # Simple percentage deviation
        if avg_amount > 0:
            deviation = (abs(amount - avg_amount) / avg_amount) * 100
            
            # If deviation is more than 200% (significant)
            if deviation > 200:
                score = min(100, deviation / 5) # Scale deviation to 0-100 range roughly
                reasons.append(f"Statistical anomaly: Amount deviates {int(deviation)}% from user average.")
            else:
                score = 0
                
        return score, reasons

    def _layer3_simulated_ml(self, l1_score, l2_score):
        """Layer 3: Simulated ML Risk Score."""
        # A simple ML simulation: probability increases sigmoidally with trigger scores
        # We simulate a "learned" relationship where layered triggers compound
        combined_triggers = (l1_score + l2_score) / 2
        
        # Sigmoid function approximation
        # Risk score = 100 / (1 + e^-k(x-x0))
        # Where x is combined triggers, x0 is the threshold (50), k is steepness (0.1)
        k = 0.1
        x0 = 50
        try:
            probability = 100 / (1 + math.exp(-k * (combined_triggers - x0)))
        except OverflowError:
            probability = 100 if combined_triggers > x0 else 0
            
        return round(probability, 2)

    def _classify_risk(self, score):
        if score <= 30:
            return "LOW"
        elif score <= 60:
            return "MEDIUM"
        else:
            return "HIGH"
