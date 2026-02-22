from user_profiler import UserProfiler
from fraud_detection_engine import FraudDetectionEngine
from financial_health_engine import FinancialHealthEngine
import json

def test_system():
    profiler = UserProfiler()
    fraud_engine = FraudDetectionEngine()
    health_engine = FinancialHealthEngine()
    
    user_id = "U_TEST"
    
    # helper to process a transaction
    def process_txn(txn, label):
        print(f"\n--- Test: {label} ---")
        current_profile = profiler.get_serializable_profile(user_id)
        
        # 1. Fraud Analysis
        f_analysis = fraud_engine.analyze_transaction(txn, current_profile)
        
        # 2. Update Profile
        profiler.update_profile(txn)
        profiler.add_risk_event(user_id, txn["timestamp"], f_analysis["final_risk_score"])
        
        # 3. Health Analysis
        updated_profile = profiler.get_serializable_profile(user_id)
        h_analysis = health_engine.calculate_health_score(updated_profile, f_analysis)
        
        print(f"Risk: {f_analysis['risk_level']} (Score: {f_analysis['final_risk_score']})")
        print(f"Trend: {f_analysis['risk_trend']} (Avg: {f_analysis['last_5_avg_risk']})")
        print(f"Health: {h_analysis['status']} (Score: {h_analysis['health_score']})")
        print(f"Health Factors: {h_analysis['factors']}")

    # Phase 1: Establish Healthy Baseline
    txns = [
        {"transaction_id": "1", "user_id": user_id, "amount": 100.0, "merchant": "Amazon", "location": "NYC", "timestamp": "2026-02-22 10:00:00"},
        {"transaction_id": "2", "user_id": user_id, "amount": 110.0, "merchant": "Uber", "location": "NYC", "timestamp": "2026-02-22 10:05:00"},
        {"transaction_id": "3", "user_id": user_id, "amount": 95.0, "merchant": "Starbucks", "location": "NYC", "timestamp": "2026-02-22 10:10:00"},
    ]
    for i, txn in enumerate(txns):
        process_txn(txn, f"Baseline Transaction {i+1}")

    # Phase 2: Suspicious Activity
    suspicious_txn = {"transaction_id": "4", "user_id": user_id, "amount": 2000.0, "merchant": "Apple", "location": "London", "timestamp": "2026-02-22 11:00:00"}
    process_txn(suspicious_txn, "High Value / New Location")

    # Phase 3: Compounding Risk (Increasing Trend)
    compounding_txn = {"transaction_id": "5", "user_id": user_id, "amount": 1500.0, "merchant": "Crypto Exchange", "location": "Paris", "timestamp": "2026-02-22 11:00:10"}
    process_txn(compounding_txn, "High Frequency / High Value / New Location")

    # Phase 4: Recovery (Decreasing Trend)
    recovery_txn = {"transaction_id": "6", "user_id": user_id, "amount": 50.0, "merchant": "Groceries", "location": "NYC", "timestamp": "2026-02-22 15:00:00"}
    process_txn(recovery_txn, "Back to Normal")

if __name__ == "__main__":
    test_system()
