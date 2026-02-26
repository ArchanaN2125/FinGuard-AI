import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_face_verification():
    print("--- 1. Testing Face Verification Trigger (Risk Score) ---")
    # Simulate a transaction that triggers high risk
    user_id = "U1"
    # Submit multiple high value transactions to spike risk and trigger biometric
    for i in range(3):
        print(f"Submitting high-value txn {i+1} at a new location...")
        res = requests.post(f"{API_BASE}/simulate", json={
            "user_id": user_id,
            "amount": 15000,
            "merchant": "LuxuryGoods",
            "location": f"UnknownCity_{i}"
        })
        time.sleep(1)
    
    print("\n--- 2. Checking Biometric Results in History ---")
    txns = requests.get(f"{API_BASE}/results").json()
    
    face_triggered = False
    for t in reversed(txns):
        if t.get('face_verification_triggered'):
            face_triggered = True
            print(f"Face Recognition Triggered for TXN {t['transaction_id']}")
            print(f"Match Status: {'SUCCESS' if t.get('face_verification_success') else 'FAILURE'}")
            print(f"Decision: {t.get('decision')}")
            break
            
    if face_triggered:
        print("SUCCESS: Risk-triggered biometric layer confirmed.")
    else:
        print("Biometric not yet triggered. Try more anomalous transactions.")

if __name__ == "__main__":
    test_face_verification()
