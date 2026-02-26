from collections import defaultdict, deque
import copy
from datetime import datetime, timedelta

class UserProfiler:
    def __init__(self):
        # Dictionary to store profiles for each user_id
        self.profiles = defaultdict(lambda: {
            "avg_amount": 0.0,
            "total_amount": 0.0,
            "transaction_count": 0,
            "location_history": set(),
            "merchant_frequency": defaultdict(int),
            "last_transaction_time": None,
            "risk_history": [],  # List of (timestamp, score)
            "adaptive_weight_factor": 1.0,
            "trusted_locations": set(),
            "trusted_merchants": set(),
            "feedback_history": [],
            "category_spending": defaultdict(float),
            "recent_txns": deque(), # 1-hour rolling window
            "seven_day_history": deque(), # Summary of txns for last 7 days
            "beneficiary_history": set(),
            "suspicious_txn_count": 0,
            "cooling_off_until": None,
            "session_risk_score": 0.0,
            "session_anomaly_score": 0.0,
            "session_risk_timeline": [], # List of (timestamp, score, tag)
            "account_balance": 50000.0, # Initial mock balance
            "avg_7d_amount": 0.0
        })

    def update_profile(self, transaction):
        """Updates the user behavior profile with safety guards."""
        user_id = transaction.get("user_id", "Unknown")
        amount = transaction.get("amount", 0.0)
        location = transaction.get("location", "Unknown")
        merchant = transaction.get("merchant", "Unknown")
        timestamp = transaction.get("timestamp")

        profile = self.profiles[user_id]

        # Update transaction statistics
        profile["transaction_count"] += 1
        profile["total_amount"] += amount
        profile["avg_amount"] = round(profile["total_amount"] / profile["transaction_count"], 2)

        # Update location history
        profile["location_history"].add(location)

        # Update merchant frequency
        profile["merchant_frequency"][merchant] += 1
        
        # Update last transaction time
        profile["last_transaction_time"] = timestamp

        # Update category spending
        category = transaction.get("category", "Uncategorized")
        profile["category_spending"][category] += amount

        # Update Rolling Window (1 hour)
        try:
            fmt = "%Y-%m-%dT%H:%M:%S"
            curr_time = datetime.strptime(timestamp, fmt)
            # Add new txn
            txn_risk = transaction.get("risk_score", 0)
            txn_data = {
                "time": curr_time,
                "amount": amount,
                "merchant": merchant,
                "risk_score": txn_risk
            }
            profile["recent_txns"].append(txn_data)
            profile["seven_day_history"].append(txn_data)
            profile["beneficiary_history"].add(merchant)
            
            # 1. Update Account Balance
            profile["account_balance"] -= amount
            
            # 2. Update cooling-off logic if suspicious
            if txn_risk > 70:
                profile["suspicious_txn_count"] += 1
                if profile["suspicious_txn_count"] >= 3:
                    profile["cooling_off_until"] = curr_time + timedelta(minutes=15)
                    profile["suspicious_txn_count"] = 0 
            
            # 3. Prune old txns
            one_hour_ago = curr_time - timedelta(hours=1)
            while profile["recent_txns"] and profile["recent_txns"][0]["time"] < one_hour_ago:
                profile["recent_txns"].popleft()
                
            seven_days_ago = curr_time - timedelta(days=7)
            while profile["seven_day_history"] and profile["seven_day_history"][0]["time"] < seven_days_ago:
                profile["seven_day_history"].popleft()

            # 4. Calculate 7-day average
            if profile["seven_day_history"]:
                profile["avg_7d_amount"] = sum(t["amount"] for t in profile["seven_day_history"]) / len(profile["seven_day_history"])

            # 5. Update session risk (rolling average)
            recent_scores = [t["risk_score"] for t in profile["recent_txns"]]
            if recent_scores:
                profile["session_risk_score"] = sum(recent_scores[-10:]) / min(10, len(recent_scores))
                
            # 6. Update session anomaly score
            profile["session_anomaly_score"] = self.calculate_session_anomaly(user_id)
        except:
            pass

        return self.get_serializable_profile(user_id)

    def calculate_session_anomaly(self, user_id):
        """Combines multiple factors into a session_anomaly_score."""
        profile = self.profiles[user_id]
        metrics = self.get_rolling_metrics(user_id)
        
        # Factors: Velocity, Cumulative Outflow, Risk Memory
        velocity_factor = min(1.0, metrics.get("txn_count_30m", 0) / 10) * 40
        outflow_factor = min(1.0, metrics.get("total_spend_30m", 0) / 5000) * 30
        risk_history_factor = min(1.0, metrics.get("avg_risk_1h", 0) / 100) * 30
        
        anomaly_score = velocity_factor + outflow_factor + risk_history_factor
        return round(min(100, anomaly_score), 2)

    def get_rolling_metrics(self, user_id):
        """Calculates behavioral metrics from the last 1 hour of activity."""
        profile = self.profiles[user_id]
        recent = list(profile["recent_txns"])
        
        if not recent:
            return {
                "total_spend_1h": 0.0,
                "txn_count_30m": 0,
                "avg_risk_1h": 0.0,
                "recent_merchants": []
            }

        now = recent[-1]["time"]
        thirty_mins_ago = now - timedelta(minutes=30)
        fifteen_mins_ago = now - timedelta(minutes=15)
        five_mins_ago = now - timedelta(minutes=5)
        
        spend_1h = sum(t["amount"] for t in recent)
        spend_30m = sum(t["amount"] for t in recent if t["time"] >= thirty_mins_ago)
        count_30m = sum(1 for t in recent if t["time"] >= thirty_mins_ago)
        count_15m = sum(1 for t in recent if t["time"] >= fifteen_mins_ago)
        count_5m = sum(1 for t in recent if t["time"] >= five_mins_ago)
        count_5m_suspicious = sum(1 for t in recent if t["time"] >= five_mins_ago and t.get("risk_score", 0) >= 70)
        
        avg_risk = sum(t["risk_score"] for t in recent) / len(recent)
        recent_merchants = [t["merchant"] for t in recent]

        return {
            "total_spend_1h": round(spend_1h, 2),
            "total_spend_30m": round(spend_30m, 2),
            "txn_count_30m": count_30m,
            "txn_count_15m": count_15m,
            "txn_count_5m": count_5m,
            "txn_count_5m_suspicious": count_5m_suspicious,
            "avg_risk_1h": round(avg_risk, 2),
            "recent_merchants": recent_merchants,
            "account_balance": profile["account_balance"],
            "avg_7d_amount": profile["avg_7d_amount"]
        }

    def add_risk_event(self, user_id, timestamp, risk_score, amount=0, merchant="Unknown", analysis=None):
        """Adds a risk event to the user's evolution timeline with structured info."""
        profile = self.profiles[user_id]
        
        # 1. Standard History (Historical Snapshot)
        profile["risk_history"].append({
            "timestamp": timestamp,
            "score": risk_score,
            "amount": amount,
            "merchant": merchant
        })
        
        # 2. Structured Session Timeline (Live Monitoring)
        if analysis:
            profile["session_risk_timeline"].append({
                "timestamp": timestamp,
                "score": risk_score,
                "primary_tag": analysis.get("primary_tag", "Normal"),
                "confidence": analysis.get("confidence_score", 100),
                "breakdown": analysis.get("risk_breakdown", {}),
                "counterfactual": analysis.get("counterfactual", "")
            })

    def apply_feedback(self, user_id, transaction, feedback):
        """Adjusts user profile weights with strict safety overrides."""
        profile = self.profiles[user_id]
        learning_rate = 0.05
        
        # 1. Safety Gate: Cooling-off check
        if profile["cooling_off_until"]:
            if datetime.now() < profile["cooling_off_until"]:
                return "Feedback restricted: Cooling-off period active due to multiple suspicious activities."
        
        event = {
            "transaction_id": transaction.get("transaction_id", "Unknown"),
            "timestamp": transaction.get("timestamp"),
            "feedback": feedback,
            "effect": ""
        }

        if feedback.upper() == "LEGITIMATE":
            # 2. Gradual reduction (0.95 multiplier) with a 0.75 floor
            new_factor = profile["adaptive_weight_factor"] * 0.95
            profile["adaptive_weight_factor"] = max(0.75, new_factor)
            
            # No immediate whitelisting, just record trust pulse
            profile["trusted_locations"].add(transaction.get("location", "Unknown"))
            profile["trusted_merchants"].add(transaction.get("merchant", "Unknown"))
            event["effect"] = f"Safe Adjustment: Factor reduced to {round(profile['adaptive_weight_factor'], 2)}."
        
        elif feedback.upper() == "FRAUD":
            # More aggressive upward for safety
            profile["adaptive_weight_factor"] = min(2.5, profile["adaptive_weight_factor"] + 0.1)
            # Active cooling off on fraud feedback
            profile["cooling_off_until"] = datetime.now() + timedelta(minutes=15)
            event["effect"] = f"Protective Trigger: Factor raised to {round(profile['adaptive_weight_factor'], 2)} and cooling-off applied."

        profile["feedback_history"].append(event)
        return event["effect"]

    def get_serializable_profile(self, user_id):
        """Returns a JSON-serializable version of a user's profile."""
        profile = self.profiles[user_id]
        return {
            "user_id": user_id,
            "average_spending": profile["avg_amount"],
            "total_transactions": profile["transaction_count"],
            "location_history": list(profile["location_history"]),
            "merchant_frequency": dict(profile["merchant_frequency"]),
            "last_transaction_time": profile["last_transaction_time"],
            "risk_history": profile["risk_history"],
            "adaptive_weight_factor": profile["adaptive_weight_factor"],
            "trusted_locations": list(profile["trusted_locations"]),
            "trusted_merchants": list(profile["trusted_merchants"]),
            "feedback_history": profile["feedback_history"],
            "category_spending": dict(profile["category_spending"]),
            "session_risk_score": profile["session_risk_score"],
            "session_anomaly_score": profile["session_anomaly_score"],
            "session_risk_timeline": profile.get("session_risk_timeline", []),
            "account_balance": profile["account_balance"],
            "is_cooled_off": profile["cooling_off_until"] > datetime.now() if profile["cooling_off_until"] else False
        }

    def get_profile_snapshot(self, user_id):
        """Returns a deep-copied serializable snapshot of the user profile."""
        # Use existing serializable logic and ensure it's a completely independent copy
        return copy.deepcopy(self.get_serializable_profile(user_id))
