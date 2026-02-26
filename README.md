# 🛡️ FinGuard AI - Real-Time Fraud Detection

FinGuard AI is an enterprise-grade fraud detection system built on the **Pathway Streaming Framework**. It monitors transaction streams in real-time, applying adaptive risk scores and biometric security gates.

## 🏆 Hackathon Compliance (Pathway Framework)
This project is a **Real-Time Streaming Application**. It does NOT use polling, manual loops, or static data processing for its risk engine.

### Core Pathway Features:
- **`mode="streaming"`**: Live ingestion of transaction data.
- **Stateful User Profiling**: Real-time aggregation of spending behavior.
- **Sliding Window Velocity**: 5-minute rolling counts to detect rapid-fire attacks.
- **Unified Risk UDF**: Fraud detection logic is embedded directly into the Pathway transformation graph.

## 🚀 Quick Start (Submission Guide)

### 🚨 PREREQUISITES
Pathway requires **Linux (Ubuntu/Debian) or WSL/Docker on Windows**. It will NOT run natively on Windows (Python will install a stub/fake package).

### Installation
```bash
pip install -r requirements.txt
```

### Execution (Production Mode)
Run these commands in separate terminals:

1. **Pathway Engine**: Processes streaming data.
   ```bash
   python pathway_pipeline.py
   ```
2. **Backend API**: Serves risk results.
   ```bash
   uvicorn api_main:app --host 0.0.0.0 --port 8000
   ```
3. **Frontend Dashboard**: Visualizes the risk feed.
   ```bash
   streamlit run streamlit_app.py
   ```

## 📍 Compliance Reference (In `pathway_pipeline.py`)
- **Streaming Setup**: Line 42 (`mode="streaming"`)
- **Stateful Joins**: Line 79
- **Windowed Analytics**: Line 150 (`pw.windows.sliding`)
- **Framework Launch**: Line 193 (`pw.run()`)

---
### 🛠️ Local Testing on Windows
If you are evaluating this project on a Windows machine without WSL, we have provided `windows_compliance_mock.py`. This mimics the Pathway interface for UI/UX testing only. For the **True Streaming Evaluation**, please refer to `pathway_pipeline.py`.
