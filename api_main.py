import asyncio
import threading
import time
import json
import uuid
import random
import requests
import copy
import os
from datetime import datetime
from collections import deque
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from user_profiler import UserProfiler
from fraud_detection_engine import FraudDetectionEngine
from financial_health_engine import FinancialHealthEngine
from rag_explainability import RAGExplainabilityLayer
from alert_manager import AlertManager

app = FastAPI(title="FinGuard AI - Risk Analyst API (Safety-First Architecture)")

# PATHWAY CONFIG
PATHWAY_URL = "http://localhost:8001"

# Global State
profiler = UserProfiler()
fraud_engine = FraudDetectionEngine()
health_engine = FinancialHealthEngine()
rag_layer = RAGExplainabilityLayer(profiler)
alert_manager = AlertManager(risk_threshold=60)

# Memory Storage for API requests
recent_transactions = deque(maxlen=50)
txn_lookup = {} # transaction_id -> txn_object
processed_txn_ids = set() # To avoid double-counting in profiler

# Configuration for simulation
USERS = ["U1", "U2", "U3"]
MERCHANTS = {
    "Big Basket": "groceries", 
    "MakeMyTrip": "travel", 
    "PVR Cinemas": "entertainment",
    "Amazon": "shopping", 
    "Binance": "crypto", 
    "Electricity Board": "utilities",
    "Netflix": "entertainment", 
    "Uber": "travel", 
    "Airtel": "utilities", 
    "Nike": "shopping"
}
LOCATIONS = ["New York, NY", "Los Angeles, CA", "London, UK", "Paris, FR", "Tokyo, JP"]

class TransactionItem(BaseModel):
    user_id: str
    amount: float
    merchant: str
    category: str
    location: str
    timestamp: str = None

class FeedbackRequest(BaseModel):
    transaction_id: str
    feedback: str # LEGITIMATE | FRAUD
    pin_confirmed: bool = False
    beneficiary_confirmed: bool = False

class SimulationRequest(BaseModel):
    user_id: str
    amount: float
    merchant: str
    category: str
    location: str

class ChatRequest(BaseModel):
    user_id: str
    query: str
    transaction_id: str = None
    is_simulation: bool = False

class PreCheckRequest(BaseModel):
    user_id: str
    amount: float
    merchant: str
    location: str

class IntentConfirmation(BaseModel):
    user_id: str
    transaction_id: str
    is_suspicious: bool # True if user answers "Yes" to scam prompts

class BiometricVerification(BaseModel):
    user_id: str
    transaction_id: str
    success: bool

def verify_face():
    """Simulates millisecond-level biometric processing."""
    time.sleep(random.uniform(0.1, 0.2)) # Simulate < 200ms latency
    # In a real app, this would interface with a face recognition SDK
    # For simulation, we assume 95% success rate for the 'primary' user
    return random.random() < 0.95

def generate_transaction():
    """Generates a realistic transaction with ISO 8601 timestamp."""
    user_id = random.choice(USERS)
    merchant, category = random.choice(list(MERCHANTS.items()))
    
    # Increase probability of outliers for testing
    rand = random.random()
    if rand < 0.15: # 15% chance of high amount
        amount_range = (2500.0, 8000.0)
    elif rand < 0.20: # 5% chance of EXTREME amount
        amount_range = (12000.0, 25000.0)
    else:
        amount_range = (5.0, 800.0)
    
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": round(random.uniform(*amount_range), 2),
        "merchant": merchant,
        "category": category,
        "location": random.choice(LOCATIONS),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

import csv

def run_simulation():
    """Background task to simulate real-time transaction ingestion using robust CSV quoting."""
    while True:
        try:
            txn = generate_transaction()
            # Prepare row for CSV
            row = [
                txn['transaction_id'], 
                txn['user_id'], 
                txn['amount'], 
                txn['merchant'], 
                txn['category'], 
                txn['location'], 
                txn['timestamp']
            ]
            
            with open("transactions.csv", "a", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(row)
            
            print(f"[Sim] Row Injected: {txn['transaction_id']} | Amount: {txn['amount']}")
            time.sleep(3)
        except Exception as e:
            with open("sim_error.log", "a") as f:
                f.write(f"{datetime.now()}: {str(e)}\n")
            time.sleep(10)

@app.on_event("startup")
def startup_event():
    """Starts the background simulation on API startup."""
    # Ensure CSV files exist with headers
    HEADER_TXN = ["transaction_id", "user_id", "amount", "merchant", "category", "location", "timestamp"]
    HEADER_FB = ["transaction_id", "user_id", "feedback"]
    
    if not os.path.exists("transactions.csv"):
        with open("transactions.csv", "w", newline='') as f:
            csv.writer(f).writerow(HEADER_TXN)
    if not os.path.exists("feedback.csv"):
        with open("feedback.csv", "w", newline='') as f:
            csv.writer(f).writerow(HEADER_FB)
            
    print("[FinGuard AI] Starting background transaction simulation (CSV Mode)...")
    threading.Thread(target=run_simulation, daemon=True).start()

@app.get("/")
async def root():
    return {"message": "FinGuard AI Risk Analyst API (Safety-First) is running.", "status": "ONLINE"}

# RAG Result Cache (Optimization to simulate async worker output)
rag_cache = {} # transaction_id -> rag_output

@app.get("/transactions")
async def get_transactions():
    """Fetches enriched transactions with cached RAG explanations for low latency."""
    start_time = time.time()
    try:
        # Fetch from Pathway REST Connector
        response = requests.get(f"{PATHWAY_URL}/v1/results")
        if response.status_code != 200:
            return {"error": f"Pathway results unreachable at {PATHWAY_URL}"}
            
        data = response.json()
        results = []
        for item in data:
            if not item: continue
            
            txn_id = item.get("transaction_id")
            # Pathway returns evaluation as a JSON string in analysis_json/analysis
            raw_analysis = item.get("analysis", "{}")
            try:
                analysis = json.loads(raw_analysis)
            except:
                analysis = {}

            # ASYNC RAG WORKER SIMULATION (Cached result check)
            if txn_id not in rag_cache:
                txn_for_rag = {
                    "transaction_id": txn_id,
                    "user_id": item.get("user_id"),
                    "amount": item.get("amount"),
                    "merchant": item.get("merchant"),
                    "location": item.get("location"),
                    "timestamp": item.get("timestamp")
                }
                user_id = item.get("user_id")
                serial_profile = profiler.get_serializable_profile(user_id) if user_id else None
                
                # Enrich profiler state if new
                if txn_id not in processed_txn_ids:
                    profiler.update_profile(txn_for_rag)
                    profiler.add_risk_event(
                        user_id, 
                        item.get("timestamp"), 
                        analysis.get("final_risk_score", 0), 
                        amount=item.get("amount", 0), 
                        merchant=item.get("merchant", "Unknown"),
                        analysis=analysis
                    )
                    processed_txn_ids.add(txn_id)
                
                # Update local lookup for chat context
                txn_lookup[txn_id] = {
                    "transaction_id": txn_id,
                    "user_id": user_id,
                    "amount": item.get("amount"),
                    "merchant": item.get("merchant"),
                    "location": item.get("location"),
                    "timestamp": item.get("timestamp"),
                    "analysis": analysis
                }

                # In a real system, this happens in a background worker
                rag_cache[txn_id] = rag_layer.explain_transaction(txn_for_rag, "Analyze", analysis, user_profile=serial_profile)

            cached_rag = rag_cache[txn_id]
            risk_score = analysis.get("final_risk_score", 0)
            decision = item.get("decision", "APPROVED")

            results.append({
                "transaction_id": txn_id,
                "timestamp": item.get("timestamp"),
                "user_id": item.get("user_id"),
                "amount": item.get("amount"),
                "merchant": item.get("merchant"),
                "location": item.get("location"),
                "risk_score": risk_score,
                "confidence_score": analysis.get("confidence_score", 0),
                "primary_tag": analysis.get("primary_tag", "N/A"),
                "risk_breakdown": analysis.get("risk_breakdown", {}),
                "counterfactual": analysis.get("counterfactual", ""),
                "risk_level": analysis.get("risk_level", "LOW"),
                "risk_category": analysis.get("risk_category", "Unknown"),
                "risk_trend": analysis.get("risk_trend", "STABLE"),
                "health_score": 100 - risk_score,
                "health_status": "HEALTHY" if risk_score < 40 else "MODERATE" if risk_score < 70 else "RISKY",
                "explanation": cached_rag.get("explanation", "AI analysis pending."),
                "supporting_evidence": cached_rag.get("supporting_evidence", []),
                "full_response": cached_rag.get("full_response", ""),
                "triggered_rules": analysis.get("reasons", []),
                "decision": decision,
                "session_anomaly_score": profiler.profiles.get(item.get("user_id"), {}).get("session_anomaly_score", 0),
                "face_verification_triggered": analysis.get("face_verification_triggered", False),
                "face_verification_success": analysis.get("face_verification_success", True),
                "is_simulation": False,
                "profile": profiler.get_serializable_profile(item.get("user_id")) # Pass full profile for timeline
            })
        
        latency = (time.time() - start_time) * 1000
        if latency > 500: # Log high latency
            print(f"[Performance] Heavy /transactions fetch: {round(latency, 2)}ms")
            
        return results[::-1] # Newest first
    except Exception as e:
        return {"error": str(e)}

@app.post("/simulate")
async def simulate_transaction(request: SimulationRequest):
    """Predicts risk for a hypothetical transaction without modifying any state."""
    # 1. SIMULATION ISOLATION - Create deep copy of the user profile
    user_id = request.user_id
    real_profile = profiler.get_profile_snapshot(user_id) # Use the snapshot method we saw in user_profiler
    profile_copy = copy.deepcopy(real_profile)
    
    txn = {
        "transaction_id": f"SIM-{uuid.uuid4()}",
        "user_id": user_id,
        "amount": request.amount,
        "merchant": request.merchant,
        "category": request.category,
        "location": request.location,
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }
    
    # 2. Perform stateless analysis using the engine (Inject rolling metrics from real profile)
    profile_copy["rolling_metrics"] = profiler.get_rolling_metrics(user_id)
    analysis = fraud_engine.analyze_transaction(txn, profile_copy, is_simulation=True)
    health_res = health_engine.calculate_health_score(profile_copy, analysis)
    
    # 3. Use the ISOLATED profile for RAG explanation
    explanation = rag_layer.explain_transaction(txn, "Simulate Risk", analysis, user_profile=profile_copy)
    
    risk_score = analysis.get("final_risk_score", 0)
    
    # 4. PRE-TRANSACTION RISK GATE FOR SIMULATION
    if risk_score > 85:
        sim_decision = "BLOCKED"
    elif 60 <= risk_score <= 85:
        sim_decision = "VERIFICATION_REQUIRED"
    else:
        sim_decision = "APPROVED"

    return {
        "predicted_risk_score": risk_score,
        "predicted_risk_level": analysis.get("risk_level"),
        "predicted_health_impact": f"{health_res.get('status')} (Score: {health_res.get('health_score')})",
        "simulation_explanation": explanation.get("explanation"),
        "supporting_evidence": explanation.get("supporting_evidence"),
        "full_response": explanation.get("full_response"),
        "predicted_decision": sim_decision,
        "is_simulation": True
    }

@app.post("/feedback")
async def post_feedback(request: FeedbackRequest):
    """Handles user feedback with multi-layered safety overrides."""
    txn_id = request.transaction_id
    
    # 1. Verification: Get the transaction and user profile
    txn = txn_lookup.get(txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found for feedback.")
    
    user_id = txn.get("user_id", "U1")
    profile = profiler.get_serializable_profile(user_id)
    
    # 2. Session Risk Override
    session_risk = profile.get("session_risk_score", 0)
    if session_risk > 80 and request.feedback.upper() == "LEGITIMATE":
        raise HTTPException(status_code=403, detail="High-risk session detected. Feedback temporarily restricted for safety.")
        
    # 3. Cooling-off Check
    if profile.get("is_cooled_off"):
        raise HTTPException(status_code=403, detail="Feedback system cooling down. Please try again in a few minutes.")

    # 4. Progressive Confirmation Layer
    txn_risk = txn.get("analysis", {}).get("final_risk_score", 0)
    if txn_risk > 70 and request.feedback.upper() == "LEGITIMATE":
        if not request.pin_confirmed or not request.beneficiary_confirmed:
            return {
                "status": "CONFIRMATION_REQUIRED",
                "message": "Secondary confirmation needed for high-risk feedback. Please re-enter PIN and confirm beneficiary."
            }

    # 5. Apply adaptive logic (via profiler for immediate local state)
    status_msg = profiler.apply_feedback(user_id, txn, request.feedback)
    
    # 6. Queue for Pathway (CSV append)
    with open("feedback.csv", "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([txn_id, user_id, request.feedback.upper()])
    
    return {
        "status": "FEEDBACK_PROCESSED",
        "message": status_msg
    }

@app.post("/precheck")
async def pre_transaction_check(request: PreCheckRequest):
    """
    Synchronous low-latency risk gate. 
    Decoupled from RAG/LLM for sub-100ms response times.
    """
    user_id = request.user_id
    txn = {
        "amount": request.amount,
        "merchant": request.merchant,
        "location": request.location
    }
    
    # Fetch profile
    profile = profiler.get_serializable_profile(user_id)
    if not profile:
        profile = {"user_id": user_id, "average_spending": 100, "risk_history": [], "location_history": []}
    
    # 1. RISK ANALYSIS (Sync Path)
    profile["rolling_metrics"] = profiler.get_rolling_metrics(user_id)
    analysis = fraud_engine.analyze_transaction(txn, profile)
    risk_score = analysis.get("final_risk_score", 0)
    
    # 2. DECISION GATE
    decision = "APPROVED"
    if risk_score > 85:
        decision = "BLOCKED"
    elif risk_score > 60:
        decision = "VERIFICATION_REQUIRED"
        
    return {
        "user_id": user_id,
        "risk_score": risk_score,
        "risk_level": analysis.get("risk_level", "LOW"),
        "decision": decision,
        "latency_mode": "SYNC_LOW_LATENCY"
    }

@app.post("/chat")
async def chat_with_analyst(request: ChatRequest):
    """Interactive conversational analysis powered by RAG."""
    # Safety Check: Read-only context
    user_id = request.user_id
    
    # 1. Isolation Handling
    if request.is_simulation:
        profile = profiler.get_profile_snapshot(user_id)
    else:
        profile = profiler.get_serializable_profile(user_id)
        
    # 2. Coordinate with RAG Layer
    txn_snapshot = None
    if request.transaction_id:
        txn_snapshot = txn_lookup.get(request.transaction_id)
    
    # Debug Logs
    print(f"DEBUG - Snapshot: {txn_snapshot.get('transaction_id') if txn_snapshot else 'None'}")
    print(f"DEBUG - Profile Hist: {len(profile.get('risk_history', []))} events")

    chat_results = rag_layer.chat_analysis(
        query=request.query,
        user_id=user_id,
        transaction=txn_snapshot,
        user_profile=profile
    )
    
    return chat_results

@app.post("/confirm_intent")
async def confirm_intent(request: IntentConfirmation):
    """Handles psychological interruption session responses."""
    user_id = request.user_id
    if request.is_suspicious:
        # Immediately spike risk for this user
        profiler.profiles[user_id]["adaptive_weight_factor"] = min(2.5, profiler.profiles[user_id]["adaptive_weight_factor"] + 0.3)
        profiler.profiles[user_id]["session_anomaly_score"] = 100.0
        return {"status": "RISK_ESCALATED", "message": "High-risk intent detected. Session restricted."}
    
    return {"status": "PROCEED", "message": "Intent acknowledged. Vigilance maintained."}
