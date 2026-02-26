import streamlit as st
import pandas as pd
import requests
import time
import copy
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="FinGuard AI | Streamlit Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# API Base URL
API_BASE = "http://localhost:8000"
CURRENCY_SYMBOL = "₹"

def fetch_data(endpoint):
    try:
        response = requests.get(f"{API_BASE}/{endpoint}")
        if response.status_code == 200:
            return response.json()
    except Exception:
        return None
    return None

def color_risk(val):
    if val == "HIGH":
        return 'background-color: #f43f5e; color: white'
    elif val == "MEDIUM":
        return 'background-color: #fbbf24; color: black'
    elif val == "LOW":
        return 'background-color: #10b981; color: white'
    return ''

# Sidebar - Controls
st.sidebar.title("🛡️ FinGuard AI Control")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 3, 15, 5)

# Initialize Session State
if 'is_paused' not in st.session_state:
    st.session_state.is_paused = False
if 'analysis_snapshot' not in st.session_state:
    st.session_state.analysis_snapshot = None
if 'selected_txn_id' not in st.session_state:
    st.session_state.selected_txn_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

def toggle_pause():
    st.session_state.is_paused = not st.session_state.is_paused

pause_label = "▶️ Resume Live UI" if st.session_state.is_paused else "⏸️ Pause Live UI"
st.sidebar.button(pause_label, on_click=toggle_pause, use_container_width=True)

user_id = st.sidebar.selectbox("Focus User", ["All Users", "U1", "U2", "U3"])

# UI Layout with Tabs for Isolation
st.title("Enterprise Risk Intelligence Dashboard")
tab_monitor, tab_investigate = st.tabs(["📺 Live Monitor", "🕵️ Investigation"])

# Logic for Simulation Loop (Data Fetching)
# We fetch data at the start of each rerun to keep 'Live Monitor' current
data = fetch_data("transactions")
if isinstance(data, list):
    st.session_state.transactions = data[:50]
    txns = st.session_state.transactions
    if user_id != "All Users":
        txns = [t for t in txns if t['user_id'] == user_id]
else:
    txns = []

with tab_monitor:
    st.subheader("Real-Time Risk Feed")
    if txns:
        df = pd.DataFrame(txns).head(20)
        
        # Metrics
        m1, m2, m3 = st.columns(3)
        first_txn = txns[0]
        m1.metric("Latest Risk", f"{first_txn.get('risk_score', 'N/A')}", first_txn.get('risk_trend', 'STABLE'))
        m2.metric("Avg Health", f"{df['health_score'].mean():.1f}")
        m3.metric("Total Flagged", len(df[df['risk_level'] == 'HIGH']))

        # Chart & Feed
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Risk Evolution")
            chart_df = df[['timestamp', 'risk_score']].copy()
            try:
                chart_df['timestamp'] = pd.to_datetime(chart_df['timestamp'])
                st.line_chart(chart_df.sort_values('timestamp').set_index('timestamp'), height=300)
            except Exception as e:
                st.error(f"Chart error: {str(e)}")
                st.write("Retrying to parse data...")
        
        with c2:
            st.subheader("Recent Activity")
            cols = ['timestamp', 'merchant', 'amount', 'risk_score', 'risk_level', 'decision']
            st.dataframe(df[cols].style.applymap(color_risk, subset=['risk_level']), use_container_width=True, height=300)
    else:
        st.info("⌛ Waiting for live data stream...")

with tab_investigate:
    st.subheader("Immutable Transaction Investigation")
    
    # 1. Selection Area (Uses global state pool)
    available = st.session_state.transactions
    if available:
        txn_ids = [t.get('transaction_id') for t in available if t.get('transaction_id')]
        
        # Determine current index for selectbox persistence
        current_idx = None
        if st.session_state.selected_txn_id in txn_ids:
            current_idx = txn_ids.index(st.session_state.selected_txn_id)

        selected_id = st.selectbox(
            "Select TXN for Stable Snapshot:",
            options=txn_ids,
            index=current_idx,
            placeholder="Choose a transaction...",
            format_func=lambda x: f"{next((t.get('merchant', 'Unknown') for t in available if t.get('transaction_id') == x), 'Unknown')} | {CURRENCY_SYMBOL}{next((t.get('amount', 0) for t in available if t.get('transaction_id') == x), 0)} | {next((t.get('risk_level', 'Unknown') for t in available if t.get('transaction_id') == x), 'Unknown')}",
            key="investigate_selector"
        )
        
        # Create Snapshot on Selection Change
        if selected_id and selected_id != st.session_state.selected_txn_id:
            st.session_state.selected_txn_id = selected_id
            target = next((t for t in available if t.get('transaction_id') == selected_id), None)
            if target:
                # IMMUTABLE SNAPSHOT: copy.deepcopy
                st.session_state.analysis_snapshot = copy.deepcopy(target)
                st.session_state.chat_history = [] # Clear history for new snapshot
    else:
        st.warning("No transactions available. Please wait for Live Monitor to populate.")

    # 2. Deep Dive (Uses Snapshot ONLY)
    if st.session_state.analysis_snapshot:
        snap = st.session_state.analysis_snapshot
        st.markdown(f"### 🔍 Deep Dive: `{snap['transaction_id']}`")
        
        col_meta, col_diag, col_bio = st.columns([1, 1.5, 0.5])
        with col_meta:
            st.write(f"**User**: {snap['user_id']}")
            st.write(f"**Amount**: {CURRENCY_SYMBOL}{snap['amount']}")
            st.write(f"**Confidence**: {snap.get('confidence_score', 0)}%")
            st.write(f"**Primary Cause**: {snap.get('primary_tag', 'N/A')}")
            st.write(f"**Decision**: {snap.get('decision', 'N/A')}")
            st.write(f"**Location**: {snap['location']}")
            st.write(f"**Timestamp**: {snap['timestamp']}")

        with col_diag:
            st.info(snap.get('full_response', 'AI analysis pending.'))
            
        with col_bio:
            if snap.get('face_verification_triggered'):
                st.markdown("📷 **Face Recognition**")
                if snap.get('face_verification_success'):
                    st.success("MATCH")
                else:
                    st.error("MISMATCH")
            else:
                st.markdown("📷 **Biometric**")
                st.write("OFF (Low Risk)")
            
            breakdown = snap.get('risk_breakdown', {})
            if breakdown:
                st.markdown("---")
                st.markdown("**Risk Decomposition**")
                import pandas as pd
                df_break = pd.DataFrame(list(breakdown.items()), columns=["Signal", "Risk Contribution"])
                st.bar_chart(df_break.set_index("Signal"))
            
        # Advanced Safety Gates
        txn_risk = snap.get('risk_score', 0)
        session_anomaly = snap.get('session_anomaly_score', 0)
        
        # 1. Psychological Interruption (65-85 range)
        if 65 <= txn_risk <= 85:
            st.warning("🕵️ **Security Alert: Potential Scam Detected**")
            st.info("Is someone asking you to transfer money urgently? Are you on a call while making this payment?")
            c_yes, c_no = st.columns(2)
            if c_yes.button("⚠️ Yes, I'm being guided", key="intent_yes"):
                requests.post(f"{API_BASE}/confirm_intent", json={"user_id": snap['user_id'], "transaction_id": snap['transaction_id'], "is_suspicious": True})
                st.error("Protocol: HIGH RISK. Session Restricted.")
                st.rerun()
            if c_no.button("✅ No, this is my own choice", key="intent_no"):
                requests.post(f"{API_BASE}/confirm_intent", json={"user_id": snap['user_id'], "transaction_id": snap['transaction_id'], "is_suspicious": False})
                st.success("Acknowledged. Continue with caution.")

        # 2. Biometric Control (> 40 Session Anomaly)
        requires_biomeric = session_anomaly > 40
        face_failed = snap.get('face_verification_triggered') and not snap.get('face_verification_success')
        is_blocked = session_anomaly > 80 or txn_risk > 80 or face_failed
        
        if face_failed:
             st.error("⛔ **Transaction Blocked**: Face recognition mismatch. Funds protected before debit.")
        elif is_blocked:
            st.error("⛔ **Transaction Blocked**: High-risk session/transaction detected. Funds protected before debit.")
        elif requires_biomeric:
            st.warning("🧬 **Biometric Confirmation Required**: Please use your device's biometric scanner or enter FaceID.")
        
        # 3. Session Risk Timeline
        st.markdown("---")
        st.markdown("### 📈 Recent Session Risk (Last 10)")
        profile = snap.get('profile', {})
        timeline = profile.get('session_risk_timeline', [])
        if timeline:
            # Show last 10 for better UX
            for event in timeline[-10:][::-1]:
                col1, col2, col3 = st.columns([1.5, 1, 1])
                col1.write(f"🕒 {event['timestamp']}")
                col2.write(f"⚖️ Score: {event['score']}")
                col3.write(f"🏷️ {event['primary_tag']}")
        else:
            st.write("No session timeline data available.")
            if st.button("🤳 Simulate Biometric Success", key="biometric_btn"):
                st.session_state.biometric_success = True
                st.success("Biometrics Verified.")

        # 3. Feedback Logic with Layered Gates
        requires_confirm = txn_risk > 50
        
        with st.container():
            # Only show feedback if not blocked
            if not is_blocked:
                # If biometric required, must pass it first
                if requires_biomeric and not st.session_state.get('biometric_success'):
                    st.info("Verify biometrics to enable investigation actions.")
                else:
                    if requires_confirm:
                        st.warning("⚠️ High-Risk Transaction: Secondary confirmation required for 'Legitimate' status.")
                        col_pin, col_ben = st.columns(2)
                        sim_pin = col_pin.text_input("Re-enter SIM PIN (1234):", type="password", key="feedback_pin")
                        confirm_ben = col_ben.checkbox("Confirm Beneficiary Name Matches", key="feedback_ben")
                    
                    f1, f2 = st.columns(2)
                    if f1.button("✅ Legitimate", key="legit_btn"):
                        payload = {
                            "transaction_id": snap['transaction_id'], 
                            "feedback": "LEGITIMATE",
                            "pin_confirmed": sim_pin == "1234" if requires_confirm else True,
                            "beneficiary_confirmed": confirm_ben if requires_confirm else True
                        }
                        res = requests.post(f"{API_BASE}/feedback", json=payload)
                        if res.status_code == 200:
                            data = res.json()
                            if data.get("status") == "CONFIRMATION_REQUIRED":
                                st.error(data.get("message"))
                            else:
                                st.success(data.get("message", "State updated."))
                        elif res.status_code == 403:
                            st.error(res.json().get("detail", "Feedback blocked by safety system."))
                        else:
                            st.error("Failed to process feedback.")

                    if f2.button("🚫 Fraud", key="fraud_btn"):
                        requests.post(f"{API_BASE}/feedback", json={"transaction_id": snap['transaction_id'], "feedback": "FRAUD"})
                        st.error("Flagged as Fraud. Cooling-off applied.")

        # 3. AI Analyst Chat (Uses Snapshot Context)
        st.markdown("---")
        st.write("💬 **Interactive AI Analyst (Snapshot Mode)**")
        
        with st.form("ai_analyst_form", clear_on_submit=True):
            chat_query = st.text_input("Ask about this snapshot:", placeholder="e.g. Why was the amount flagged?")
            submitted = st.form_submit_button("🚀 Run Analysis")
            
            if submitted and chat_query:
                with st.spinner("Analyzing snapshot..."):
                    res = requests.post(f"{API_BASE}/chat", json={
                        "user_id": snap['user_id'],
                        "query": chat_query,
                        "transaction_id": snap['transaction_id']
                    })
                    if res.status_code == 200:
                        st.session_state.chat_history.append({"q": chat_query, "a": res.json().get("response")})
        
        # Display History (Persistent across refreshes)
        for chat in reversed(st.session_state.chat_history):
            with st.expander(f"Q: {chat['q']}", expanded=True):
                st.info(chat['a'])
                
        # 4. Experimental: What-If Simulation
        st.markdown("---")
        with st.expander("🧪 What-If Prediction", expanded=True):
            counterfactual = snap.get('counterfactual')
            if counterfactual:
                st.info(f"👉 **Data-Driven Insight**: {counterfactual}")
                st.caption("This prediction uses your historical spending patterns to calculate how risk would change if transaction parameters were different.")
            else:
                st.write("Counterfactual analysis not available for this snapshot.")
    else:
        st.info("💡 Select a transaction above to create an immutable analysis snapshot.")


# 5. RERUN LOOP (Only if not paused)
if not st.session_state.is_paused:
    # We always rerun at the bottom to keep the data fresh for the 'monitor' tab.
    # Because we use snapshots and stable indices, this doesn't disrupt investigation.
    time.sleep(refresh_rate)
    st.rerun()
