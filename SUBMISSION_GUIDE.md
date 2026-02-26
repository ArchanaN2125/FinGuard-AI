# 🛡️ FinGuard AI - Pathway Framework Submission

## 🚀 Pathway Framework Integration
This project is built using the **Pathway Streaming Framework** as the core real-time AI engine. It satisfies the strict hackathon requirement of "Automatic updates when new data arrives."

### 🧠 Framework Architecture
- **Stateful Intelligence**: Using `pw.Table` stateful aggregations to maintain real-time user spending profiles.
- **Biometric Risk Gating**: A high-speed risk engine triggered automatically by the Pathway stream when risk thresholds are crossed.
- **Sliding Window Analytics**: Implemented `pw.windows.sliding` for real-time velocity detection (5-minute windows).
- **REST Exposure**: The Pathway engine exposes its real-time results via the built-in `pw.io.http.expose` framework connector.

## 🛠️ How to Run (For Judges - Linux/WSL)
The core intelligence runs on the official Pathway library.

1. **Terminal 1: Start Pathway Engine**
   ```bash
   python pathway_pipeline.py
   ```
2. **Terminal 2: Start Risk API**
   ```bash
   uvicorn api_main:app --host 0.0.0.0 --port 8000
   ```
3. **Terminal 3: Start Dashboard**
   ```bash
   streamlit run streamlit_app.py
   ```

## 📍 Where is Pathway used?
- **Schema Definition**: `pathway_pipeline.py` L12-L25
- **Streaming Ingestion**: `pathway_pipeline.py` L39-L49
- **Stateful Profiling**: `pathway_pipeline.py` L53-L91
- **Windowed Velocity**: `pathway_pipeline.py` L150-L157
- **Execution Engine**: `pathway_pipeline.py` L193 (`pw.run()`)

---
*Note: For local testing on Windows, `windows_compliance_mock.py` was used as a UI-bridge due to Pathway's Linux-native requirements. The code for submission is strictly `pathway_pipeline.py`.*
