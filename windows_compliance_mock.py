import json
import time
import threading
import os
from flask import Flask, jsonify
from fraud_detection_engine import FraudDetectionEngine

app = Flask(__name__)

# Mock State
profiles = {} # user_id -> stats
processed_txns = []
fraud_engine = FraudDetectionEngine()

import csv

def mock_pathway_logic():
    """Simulates Pathway's streaming ingestion efficiently for Windows TESTING ONLY."""
    global processed_txns
    
    print("[Windows Mock] Initializing High-Performance Stream...")
    
    TRANSACTIONS_FILE = "transactions.csv"
    FEEDBACK_FILE = "feedback.csv"
    
    last_tx_pos = 0
    last_fb_pos = 0

    while True:
        try:
            # 1. Process New Transactions (Efficient Seeking)
            if os.path.exists(TRANSACTIONS_FILE):
                with open(TRANSACTIONS_FILE, "r", newline='') as f:
                    if last_tx_pos == 0:
                        f.readline() # Skip header on first read
                    else:
                        f.seek(last_tx_pos)
                    
                    reader = csv.reader(f)
                    for row in reader:
                        if not row or len(row) < 7: continue
                        txn = {
                            "transaction_id": row[0],
                            "user_id": row[1],
                            "amount": float(row[2]),
                            "merchant": row[3],
                            "category": row[4],
                            "location": row[5],
                            "timestamp": row[6]
                        }
                        
                        uid = txn["user_id"]
                        p = profiles.setdefault(uid, {"user_id": uid, "avg_amount": 0.0, "total_transactions": 0, "location_history": [], "adaptive_weight_factor": 1.0})
                        
                        p["total_transactions"] += 1
                        p.setdefault("location_history", []).append(txn["location"])
                        p["last_transaction_time"] = txn["timestamp"]
                        
                        analysis = fraud_engine.analyze_transaction(txn, p)
                        
                        # Calculate a mock session anomaly score
                        recent_risks = [t["analysis_obj"]["final_risk_score"] for t in processed_txns if t["user_id"] == uid][-5:]
                        session_anomaly = (sum(recent_risks) / len(recent_risks)) if recent_risks else 0
                        if analysis["final_risk_score"] > 60: session_anomaly += 20
                        p["session_anomaly_score"] = min(100, session_anomaly)

                        # Biometric Trigger Logic (Matches pathway_pipeline.py)
                        score = analysis.get("final_risk_score", 0)
                        biometric_triggered = score >= 55 # Lowered even more
                        face_verified = True
                        if biometric_triggered and score > 85:
                            face_verified = False # Simulate failure for extreme risk
                            
                        analysis["face_verification_triggered"] = biometric_triggered
                        analysis["face_verification_success"] = face_verified
                        
                        decision = "APPROVED"
                        if not face_verified: decision = "BLOCKED"
                        elif score > 85: decision = "BLOCKED"
                        elif score > 60: decision = "VERIFICATION_REQUIRED"
                        
                        analysis["decision"] = decision

                        processed_txns.append({
                            "transaction_id": txn["transaction_id"],
                            "user_id": txn["user_id"],
                            "amount": txn["amount"],
                            "merchant": txn["merchant"],
                            "location": txn["location"],
                            "timestamp": txn["timestamp"],
                            "analysis": json.dumps(analysis),
                            "analysis_obj": analysis, # Added for internal mock logic
                            "decision": decision
                        })
                    last_tx_pos = f.tell()

            # 2. Process Feedback
            if os.path.exists(FEEDBACK_FILE):
                with open(FEEDBACK_FILE, "r", newline='') as f:
                    if last_fb_pos == 0:
                        f.readline()
                    else:
                        f.seek(last_fb_pos)
                    
                    reader = csv.reader(f)
                    for row in reader:
                        if not row or len(row) < 3: continue
                        uid = row[1]
                        fb_type = row[2].upper()
                        if uid in profiles:
                            if fb_type == "LEGITIMATE":
                                profiles[uid]["adaptive_weight_factor"] = max(0.7, profiles[uid]["adaptive_weight_factor"] * 0.95)
                            else:
                                profiles[uid]["adaptive_weight_factor"] = min(2.5, profiles[uid]["adaptive_weight_factor"] + 0.2)
                    last_fb_pos = f.tell()

            time.sleep(0.5) # Fast reactivity
        except Exception as e:
            print(f"Mock Error: {e}")
            time.sleep(1)

            time.sleep(1)
        except Exception as e:
            print(f"Mock Error: {e}")
            time.sleep(2)

@app.route('/v1/results', methods=['GET'])
def get_results():
    return jsonify(processed_txns[-50:])

@app.route('/v1/user_profiles', methods=['GET'])
def get_profiles():
    return jsonify(list(profiles.values()))

if __name__ == "__main__":
    threading.Thread(target=mock_pathway_logic, daemon=True).start()
    print("[Windows Mock] REST Endpoint active on http://localhost:8001")
    app.run(port=8001, debug=False, use_reloader=False)
