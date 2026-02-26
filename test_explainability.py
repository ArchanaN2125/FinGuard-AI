import requests
import time
import json

API_BASE = "http://localhost:8000"

def test_explainable_risk():
    print("--- 1. Testing Structured Risk Breakdown ---")
    user_id = "U1"
    res = requests.post(f"{API_BASE}/simulate", json={
        "user_id": user_id,
        "amount": 25000,
        "merchant": "LuxuryElectronics",
        "location": "Singapore"
    })
    
    print("\n--- 2. Fetching Enriched Results ---")
    # Wait for background processing (though /simulate is synchronous in terms of returns)
    time.sleep(2)
    txns = requests.get(f"{API_BASE}/transactions").json()
    
    latest = txns[0] if txns else {}
    print(f"Transaction: {latest.get('transaction_id')}")
    print(f"Final Risk Score: {latest.get('risk_score')}")
    print(f"Confidence Score: {latest.get('confidence_score')}%")
    print(f"Primary Tag: {latest.get('primary_tag')}")
    print(f"Risk Breakdown: {json.dumps(latest.get('risk_breakdown'), indent=2)}")
    print(f"Counterfactual: {latest.get('counterfactual')}")
    
    if latest.get('risk_breakdown'):
        print("SUCCESS: Structured risk decomposition found.")
    
    if latest.get('counterfactual'):
        print("SUCCESS: Counterfactual explanation generated.")

    print("\n--- 3. Testing Session Timeline ---")
    profile = latest.get('profile', {})
    timeline = profile.get('session_risk_timeline', [])
    if timeline:
        print(f"Session Timeline Events: {len(timeline)}")
        for event in timeline:
            print(f"- {event['timestamp']} | Score: {event['score']} | Tag: {event['primary_tag']}")
        print("SUCCESS: Session risk timeline tracked.")
    else:
        print("FAILURE: Session timeline missing.")

if __name__ == "__main__":
    test_explainable_risk()
