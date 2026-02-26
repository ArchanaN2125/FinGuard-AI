FinGuard AI
Real-Time Fraud Prevention System using Pathway

Project Overview
FinGuard AI is a real-time fraud detection system that checks transactions before money leaves the user’s account.
Many traditional systems detect fraud only after the money is sent. Our system analyzes every transaction instantly and decides whether to allow, verify, or block it based on risk level.
We built this project using the Pathway framework to handle streaming transaction data and update risk scores automatically when new data arrives.

What Problem We Are Solving
Fraud today happens silently.
Sometimes money is transferred in small amounts multiple times.
Sometimes fraud happens very fast within a few minutes.
Sometimes systems only show “Suspicious” without clear explanation.

Our system focuses on:
Detecting fraud before money transfer
Identifying split transactions
Monitoring unusual behavior
Providing clear explanation for every flagged transaction

How Our System Works
A new transaction comes in.
Pathway streaming engine processes the data automatically.
Risk score is calculated based on behavior patterns.

Based on risk level:
Low → Allow
Medium → Extra confirmation
High → Biometric verification or block
AI explanation shows why the transaction was flagged.

Why We Used Pathway
We used the real Pathway library in pathway_pipeline.py.
import pathway as pw
pw.Schema
pw.io.csv.read(mode="streaming")
pw.run()
Whenever new transaction data is added, Pathway automatically updates the risk score. There are no manual loops used for refreshing.
This follows the hackathon requirement for real-time streaming.

Technologies Used
Backend:
Python
FastAPI
Pathway
Uvicorn

Frontend:
Streamlit
HTML / CSS

AI:
LLM
RAG-based explainability
Behavioral risk engine

Key Features
Pre-Transaction Risk Detection
Behavior & Velocity Monitoring
Split Fraud Detection
Progressive Risk Escalation
Biometric Trigger for High Risk
Explainable AI

How to Run the Project
Install dependencies:
pip install -r requirements.txt
Run Pathway pipeline:
python pathway_pipeline.py

Start backend:
uvicorn api_main:app --reload
Run frontend:
streamlit run streamlit_app.py

Demo Video
 https://drive.google.com/file/d/1v5SjrP0Kh4AMkRK9bspK-vfCRxFE6hro/view?usp=drivesdk
GitHub Repository
  https://github.com/ArchanaN2125/FinGuard-AI