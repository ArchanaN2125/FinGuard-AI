import json
from datetime import datetime, timedelta
from user_profiler import UserProfiler
from fraud_detection_engine import FraudDetectionEngine

def test_gradual_fraud():
    profiler = UserProfiler()
    engine = FraudDetectionEngine()
    
    user_id = "U_TEST"
    # Setup base profile
    profiler.profiles[user_id]["avg_amount"] = 50.0
    profiler.profiles[user_id]["transaction_count"] = 10
    profiler.profiles[user_id]["total_amount"] = 500.0
    
    # 1. Simulate a burst of small transactions
    base_time = datetime(2026, 2, 26, 14, 0, 0)
    for i in range(6): # 6 transactions in 5 minutes
        txn_time = base_time + timedelta(minutes=i)
        txn = {
            "transaction_id": f"T-{i}",
            "user_id": user_id,
            "amount": 20.0,
            "merchant": "Repetitive Merchant",
            "location": "New York, NY",
            "timestamp": txn_time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        
        # Get rolling metrics for the current state (before this txn is added)
        profile_data = profiler.get_serializable_profile(user_id)
        profile_data["rolling_metrics"] = profiler.get_rolling_metrics(user_id)
        
        analysis = engine.analyze_transaction(txn, profile_data)
        
        # Update profiler with current txn for next iteration
        profiler.update_profile(txn)
        
        print(f"Txn {i}: Amount {txn['amount']}, Risk Score: {analysis['final_risk_score']}, Level: {analysis['risk_level']}")
        if analysis['behavioral_risk_component'] > 0:
            print(f"  -> Behavioral Risk: {analysis['behavioral_risk_component']}")
            print(f"  -> Reasons: {analysis['reasons']}")

    # Final check
    metrics = profiler.get_rolling_metrics(user_id)
    print("\nFinal Rolling Metrics:")
    print(f"Txn Count (30m): {metrics['txn_count_30m']}")
    print(f"Total Spend (1h): {metrics['total_spend_1h']}")

if __name__ == "__main__":
    test_gradual_fraud()
