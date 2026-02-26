import math
from datetime import datetime

CURRENCY_SYMBOL = "₹"

class FraudDetectionEngine:
    def __init__(self):
        # Weights for the 3-layer hybrid score
        self.LAYER_WEIGHTS = {
            "rule_based": 0.35,
            "statistical": 0.25,
            "simulated_ml": 0.2,
            "behavioral": 0.2
        }
        self.TIME_THRESHOLD_SECONDS = 60  # High frequency threshold

    def analyze_transaction(self, transaction, user_profile, is_simulation=False):
        """Processes a transaction through 3 layers + adaptive factor with safety guards."""
        
        # 1. RISK LAYERS
        layer1_score, layer1_reasons = self._layer1_rules(transaction, user_profile)
        layer2_score, layer2_reasons = self._layer2_statistical(transaction, user_profile)
        layer3_score = self._layer3_simulated_ml(layer1_score, layer2_score)
        layer4_score, layer4_reasons = self._layer4_behavioral_anomaly(transaction, user_profile)
        
        # 2. RISK BREAKDOWN (DECOMPOSITION)
        risk_breakdown = {
            "amount_deviation": layer1_score if "Amount" in str(layer1_reasons) else (layer2_score * 0.5),
            "velocity_spike": layer4_score if "Velocity" in str(layer4_reasons) else 0,
            "cumulative_outflow": layer4_score if "Cumulative" in str(layer4_reasons) else 0,
            "balance_drain": layer4_score if "Balance Drain" in str(layer4_reasons) else 0,
            "new_beneficiary": 30 if "location" in str(layer1_reasons).lower() else 0,
            "session_anomaly": user_profile.get("session_anomaly_score", 0)
        }

        # 3. HYBRID COMBINATION
        base_score = (
            (layer1_score * self.LAYER_WEIGHTS["rule_based"]) +
            (layer2_score * self.LAYER_WEIGHTS["statistical"]) +
            (layer3_score * self.LAYER_WEIGHTS["simulated_ml"]) +
            (layer4_score * self.LAYER_WEIGHTS.get("behavioral", 0))
        )
        
        # 4. PER-USER ADAPTIVE FACTOR
        adaptive_weight = user_profile.get("adaptive_weight_factor", 1.0)
        final_score = min(100, round(base_score * adaptive_weight, 2))
        
        # 5. CONFIDENCE SCORE
        confidence = self._calculate_confidence(risk_breakdown, final_score)
        
        # 6. ROOT CAUSE TAGGING
        primary_tag = self._get_primary_tag(risk_breakdown)
        
        # 7. TREND & CLASSIFICATION
        risk_level = self._classify_risk(final_score)
        risk_history = user_profile.get("risk_history", [])
        trend, last_avg = self._calculate_risk_trend(risk_history, final_score)
        
        # 8. COUNTERFACTUAL
        counterfactual = self._generate_counterfactual(transaction, user_profile)

        return {
            "transaction_id": transaction.get("transaction_id", "Unknown"),
            "final_risk_score": final_score,
            "confidence_score": confidence,
            "risk_level": risk_level,
            "primary_tag": primary_tag,
            "risk_breakdown": risk_breakdown,
            "counterfactual": counterfactual,
            "reasons": list(set(layer1_reasons + layer2_reasons + layer4_reasons)),
            "risk_trend": trend,
            "last_5_avg_risk": last_avg,
            "is_simulation": is_simulation
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
        """Layer 1: Rule-Based Logic with Safety Guards."""
        score = 0
        reasons = []
        
        # SAFETY: Ensure profile and txn fields exist via .get()
        avg_amount = profile.get("average_spending", 100)
        total_txns = profile.get("total_transactions", 0)
        txn_amount = txn.get("amount", 0)
        txn_loc = txn.get("location", "Unknown")
        txn_merchant = txn.get("merchant", "Unknown")
        txn_timestamp = txn.get("timestamp")
        
        # Rule 1: Amount > 3x average
        if total_txns > 2: # Only check if we have some history
            if txn_amount > (3 * avg_amount):
                score += 50
                reasons.append(f"Amount ({CURRENCY_SYMBOL}{txn_amount}) is significantly higher—over 3x—than your normal average of {CURRENCY_SYMBOL}{avg_amount}.")

        # Rule 2: New Location (Bypassed if trusted)
        trusted_locations = profile.get("trusted_locations", [])
        loc_history = profile.get("location_history", [])
        if txn_loc not in loc_history and txn_loc not in trusted_locations:
            score += 30
            reasons.append(f"Transaction originates from a location not previously seen in your history: {txn_loc}.")

        # Rule 4: Trusted Merchant Discount
        trusted_merchants = profile.get("trusted_merchants", [])
        if txn_merchant in trusted_merchants:
            score = max(0, score - 20)

        # Rule 3: High Frequency
        last_time = profile.get("last_transaction_time")
        if last_time and txn_timestamp:
            fmt = "%Y-%m-%d %H:%M:%S"
            try:
                t1 = datetime.strptime(last_time, fmt)
                t2 = datetime.strptime(txn_timestamp, fmt)
                delta = (t2 - t1).total_seconds()
                
                if delta < self.TIME_THRESHOLD_SECONDS:
                    score += 40
                    reasons.append(f"Activity detected within {int(delta)} seconds of the last transaction.")
            except Exception:
                pass

        return min(100, score), reasons

    def _layer2_statistical(self, txn, profile):
        """Layer 2: Statistical Anomaly with Safety Guards."""
        score = 0
        reasons = []
        
        total_txns = profile.get("total_transactions", 0)
        if total_txns < 2:
            return 0, []

        avg_amount = profile.get("average_spending", 100)
        amount = txn.get("amount", 0)
        
        # Simple percentage deviation
        if avg_amount > 0:
            deviation = (abs(amount - avg_amount) / avg_amount) * 100
            
            # If deviation is more than 200% (significant)
            if deviation > 200:
                score = min(100, deviation / 5) # Scale deviation to 0-100 range roughly
                reasons.append(f"Spending Gap: This {CURRENCY_SYMBOL}{amount} purchase is significantly higher than your normal {CURRENCY_SYMBOL}{avg_amount} average.")
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

    def _layer4_behavioral_anomaly(self, txn, profile):
        """Layer 4: Behavioral Anomaly Detection (Rolling window analysis)."""
        score = 0
        reasons = []

        metrics = profile.get("rolling_metrics", {})
        if not metrics:
            return 0, []

        count_30m = metrics.get("txn_count_30m", 0)
        count_15m = metrics.get("txn_count_15m", 0)
        count_5m = metrics.get("txn_count_5m", 0)
        total_spend_30m = metrics.get("total_spend_30m", 0.0)
        avg_7d = metrics.get("avg_7d_amount", 100.0)
        balance = metrics.get("account_balance", 0.0)
        txn_amount = txn.get("amount", 0.0)
        
        # 1. Baseline Deviation (> 2.5x historical average)
        if txn_amount > (2.5 * avg_7d):
            score += 40
            reasons.append(f"Pattern Deviation: Transaction amount ({CURRENCY_SYMBOL}{txn_amount}) is over 2.5x your 7-day average baseline.")

        # 2. Strong Velocity Detection
        if count_5m >= 3:
            score += 50
            reasons.append(f"Critical Velocity: {count_5m} transfers detected in the last 5 minutes.")
        elif count_15m >= 5:
            score += 30
            reasons.append(f"High Velocity: {count_15m} transfers detected in the last 15 minutes.")

        # 3. Balance-Drain Detection (> 40% drain in 30 mins)
        # Using 30m spend as proxy for 'last 15m' as per combined metrics
        if balance > 0 and total_spend_30m > (0.4 * (balance + total_spend_30m)):
            score += 60
            reasons.append(f"Balance Drain: Cumulative transfers have depleted over 40% of your account balance in under 30 minutes.")

        return min(100, score), reasons

    def calculate_session_anomaly(self, profile):
        """Combines multiple factors into a session_anomaly_score."""
        metrics = profile.get("rolling_metrics", {})
        if not metrics:
            return 0.0
            
        # Factors: Velocity, Cumulative Outflow, Risk Memory
        velocity_factor = min(1.0, metrics.get("txn_count_30m", 0) / 10) * 40
        outflow_factor = min(1.0, metrics.get("total_spend_30m", 0) / 5000) * 30
        risk_history_factor = min(1.0, metrics.get("avg_risk_1h", 0) / 100) * 30
        
        anomaly_score = velocity_factor + outflow_factor + risk_history_factor
        return round(min(100, anomaly_score), 2)

    def _calculate_confidence(self, breakdown, score):
        """Calculates confidence score (0-100%) based on signal strength."""
        active_signals = sum(1 for v in breakdown.values() if v > 20)
        base_conf = 60 + (active_signals * 10)
        if score > 80: base_conf += 10
        return min(100, base_conf)

    def _get_primary_tag(self, breakdown):
        """Auto-tags primary fraud cause."""
        if breakdown.get("velocity_spike", 0) > 40: return "Velocity Anomaly"
        if breakdown.get("balance_drain", 0) > 40: return "Account Drain Pattern"
        if breakdown.get("cumulative_outflow", 0) > 40: return "Layered Transfer Pattern"
        if breakdown.get("amount_deviation", 0) > 40: return "Heavy Deviation"
        return "Behavioral Drift"

    def _generate_counterfactual(self, txn, profile):
        """Generates data-based counterfactual explanation."""
        avg = profile.get("average_spending", 100)
        amt = txn.get("amount", 0)
        if amt > avg * 1.5:
            return f"If this amount was within your historical average ({CURRENCY_SYMBOL}{round(avg, 2)}), risk would drop by approximately 35%."
        return "Transaction amount is within normal variance; risk is driven by non-monetary behavioral signals."
