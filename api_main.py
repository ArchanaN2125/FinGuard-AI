import asyncio
import json
import uuid
import random
from datetime import datetime
from collections import deque
from fastapi import FastAPI, BackgroundTasks, HTTPException
from user_profiler import UserProfiler
from fraud_detection_engine import FraudDetectionEngine
from financial_health_engine import FinancialHealthEngine
from rag_explainability import RAGExplainabilityLayer
from alert_manager import AlertManager

app = FastAPI(title="FinGuard AI - Risk Analyst API")

# Global State
profiler = UserProfiler()
fraud_engine = FraudDetectionEngine()
health_engine = FinancialHealthEngine()
rag_layer = RAGExplainabilityLayer(profiler)
alert_manager = AlertManager(risk_threshold=60)

# Memory Storage for API requests
recent_transactions = deque(maxlen=50)

# Configuration for simulation
USERS = ["U1", "U2", "U3"]
MERCHANTS = {
    "Amazon": "Electronics", "Starbucks": "Food & Beverage", "Walmart": "Groceries",
    "Apple": "Electronics", "Netflix": "Entertainment", "Uber": "Transportation",
    "Steam": "Entertainment", "Shell": "Fuel", "Whole Foods": "Groceries", "Nike": "Retail"
}
LOCATIONS = ["New York, NY", "Los Angeles, CA", "London, UK", "Paris, FR", "Tokyo, JP"]

def generate_transaction():
    """Generates a realistic transaction with ISO 8601 timestamp."""
    user_id = random.choice(USERS)
    merchant, category = random.choice(list(MERCHANTS.items()))
    amount_range = (5.0, 500.0)
    if random.random() < 0.1: amount_range = (2000.0, 5000.0)
    
    return {
        "transaction_id": str(uuid.uuid4()),
        "user_id": user_id,
        "amount": round(random.uniform(*amount_range), 2),
        "merchant": merchant,
        "category": category,
        "location": random.choice(LOCATIONS),
        "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    }

async def run_simulation():
    """Background task to simulate real-time transaction processing with dashboard schema."""
    while True:
        txn = generate_transaction()
        user_id = txn["user_id"]
        
        # 1. Behavioral Analysis
        current_profile = profiler.get_serializable_profile(user_id)
        fraud_analysis = fraud_engine.analyze_transaction(txn, current_profile)
        
        # 2. State Updates
        profiler.update_profile(txn)
        profiler.add_risk_event(user_id, txn["timestamp"], fraud_analysis["final_risk_score"])
        
        # 3. Deep Analysis
        updated_profile = profiler.get_serializable_profile(user_id)
        health_analysis = health_engine.calculate_health_score(updated_profile, fraud_analysis)
        rag_output = rag_layer.explain_transaction(txn, "Analyze Risk", fraud_analysis)
        
        # 4. Aggregation (Strict Enterprise Schema)
        output = {
            "transaction_id": str(txn["transaction_id"]),
            "timestamp": str(txn["timestamp"]),
            "user_id": str(txn["user_id"]),
            "amount": float(txn["amount"]),
            "merchant": str(txn["merchant"]),
            "location": str(txn["location"]),
            "risk_score": float(fraud_analysis["final_risk_score"]),
            "risk_level": str(fraud_analysis["risk_level"]).upper(),
            "risk_category": list(fraud_analysis["risk_category"]),
            "risk_trend": str(fraud_analysis["risk_trend"]).upper(),
            "health_score": float(health_analysis["health_score"]),
            "health_status": str(health_analysis["status"]).upper(),
            "explanation": str(rag_output["explanation"]),
            "supporting_evidence": list(rag_output["supporting_evidence"]),
            "triggered_rules": list(fraud_analysis["reasons"])
        }
        
        recent_transactions.appendleft(output)
        alert_manager.process_transaction_analysis(output)
        
        await asyncio.sleep(2)

@app.on_event("startup")
async def startup_event():
    """Starts the background simulation on API startup."""
    asyncio.create_task(run_simulation())

@app.get("/")
async def root():
    return {"message": "FinGuard AI Risk Analyst API is running.", "status": "ONLINE"}

@app.get("/transactions")
async def get_transactions():
    """Returns the latest processed transactions in dashboard format."""
    return list(recent_transactions)

@app.get("/alerts")
async def get_alerts():
    """Returns captured high-risk alerts in dashboard format."""
    return alert_manager.get_alerts()

@app.get("/user/{user_id}/risk")
async def get_user_risk(user_id: str):
    """Returns the current risk score and recent history for a user."""
    profile = profiler.get_serializable_profile(user_id)
    if not profile or not profile.get("risk_history"):
        raise HTTPException(status_code=404, detail="User not found or no history available.")
    
    current_score = profile["risk_history"][-1]["score"]
    
    return {
        "user_id": user_id,
        "current_risk_score": current_score,
        "risk_history": profile["risk_history"][-20:],
        "behavioral_summary": {
            "avg_spending": profile["average_spending"],
            "total_count": profile["total_transactions"],
            "locations_visited": len(profile["location_history"])
        }
    }

@app.get("/user/{user_id}/health")
async def get_user_health(user_id: str):
    """Returns the latest financial health diagnostic for a user."""
    profile = profiler.get_serializable_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Calculate health based on real profile averages
    # last_5_avg_risk is calculated here as the engine needs it for scoring
    scores = [h["score"] for h in profile.get("risk_history", [])[-5:]]
    avg_risk = round(sum(scores) / len(scores), 2) if scores else 0
    
    # Basic analysis context for the health engine
    context = {
        "last_5_avg_risk": avg_risk,
        "risk_trend": "STABLE", # Defaults to stable for health calculation if no active txn
        "reasons": []
    }
    
    health = health_engine.calculate_health_score(profile, context)
    
    return {
        "user_id": user_id,
        "health_score": health["health_score"],
        "health_status": health["status"],
        "diagnostic_factors": health["factors"]
    }
