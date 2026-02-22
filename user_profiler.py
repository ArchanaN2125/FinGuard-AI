from collections import defaultdict

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
            "risk_history": []  # List of (timestamp, score)
        })

    def update_profile(self, transaction):
        """Updates the user behavior profile based on a new transaction."""
        user_id = transaction["user_id"]
        amount = transaction["amount"]
        location = transaction["location"]
        merchant = transaction["merchant"]
        timestamp = transaction["timestamp"]

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

        return self.get_serializable_profile(user_id)

    def add_risk_event(self, user_id, timestamp, risk_score):
        """Adds a risk event to the user's evolution timeline."""
        self.profiles[user_id]["risk_history"].append({
            "timestamp": timestamp,
            "score": risk_score
        })

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
            "risk_history": profile["risk_history"]
        }
