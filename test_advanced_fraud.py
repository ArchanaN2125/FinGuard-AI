import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_advanced_fraud():
    print("--- 1. Testing Velocity and Balance Drain ---")
    # Simulate rapid transfers
    user_id = "U1"
    for i in range(4):
        print(f"Submitting rapid txn {i+1}...")
        res = requests.post(f"{API_BASE}/simulate", json={
            "user_id": user_id,
            "amount": 2000,
            "merchant": "RapidMerchant",
            "location": "New York"
        })
        time.sleep(1)
    
    print("\n--- 2. Checking Session Anomaly and Gate ---")
    txns = requests.get(f"{API_BASE}/results").json()
    latest = txns[-1] if txns else {}
    print(f"Latest TXN Status: {latest.get('decision', 'N/A')}")
    print(f"Session Anomaly Score: {latest.get('session_anomaly_score', 0)}")
    
    if latest.get('session_anomaly_score', 0) > 85:
        print("SUCCESS: High-risk session blocked / escalated.")

    print("\n--- 3. Testing Intent Confirmation ---")
    # Trigger intent confirmation (simulation)
    res = requests.post(f"{API_BASE}/confirm_intent", json={
        "user_id": user_id,
        "transaction_id": "test_id",
        "is_suspicious": True
    })
    print(f"Intent Confirmation Response: {res.json().get('status')}")

if __name__ == "__main__":
    test_advanced_fraud()
