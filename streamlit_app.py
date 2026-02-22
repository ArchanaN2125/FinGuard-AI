import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# Page Config
st.set_page_config(
    page_title="FinGuard AI | Streamlit Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# API Base URL
API_BASE = "http://localhost:8000"

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

# Sidebar - User Selection & Control
st.sidebar.title("🛡️ FinGuard AI Control")
refresh_rate = st.sidebar.slider("Refresh Rate (seconds)", 1, 10, 2)
user_id = st.sidebar.selectbox("Focus User", ["All Users", "U1", "U2", "U3"])

# Header
st.title("Enterprise Risk Intelligence Dashboard")
st.markdown("---")

# Empty placeholders for real-time updates
metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
chart_area = st.empty()
table_area = st.empty()

# Persistent state for history tracking (Streamlit session state)
if 'risk_history' not in st.session_state:
    st.session_state.risk_history = pd.DataFrame(columns=['Timestamp', 'Risk Score'])

# Simulation Loop
while True:
    txns = fetch_data("transactions")
    
    if txns:
        # Filter by user if selected
        if user_id != "All Users":
            txns = [t for t in txns if t['user_id'] == user_id]
            
        if txns:
            df = pd.DataFrame(txns)
            
            # 1. Metrics
            with metrics_col1:
                st.metric("Latest Risk Score", f"{txns[0]['risk_score']}", f"{txns[0]['risk_trend']}")
            with metrics_col2:
                st.metric("Avg Health Score", f"{df['health_score'].mean():.1f}")
            with metrics_col3:
                st.metric("Total Flagged Transactions", len(df[df['risk_level'] == 'HIGH']))

            # 2. Risk Evolution Chart
            with chart_area.container():
                st.subheader("Risk Evolution Over Time")
                chart_df = df[['timestamp', 'risk_score']].copy()
                chart_df['timestamp'] = pd.to_datetime(chart_df['timestamp'])
                chart_df = chart_df.sort_values('timestamp')
                st.line_chart(chart_df.set_index('timestamp'))

            # 3. Live Transaction Table
            with table_area.container():
                st.subheader("Live Transaction Intelligence Feed")
                display_df = df[[
                    'timestamp', 'merchant', 'amount', 'risk_score', 'risk_level', 'health_status'
                ]].copy()
                
                # Apply color styling
                st.dataframe(
                    display_df.style.applymap(color_risk, subset=['risk_level']),
                    use_container_width=True
                )

            # 4. AI Risk Analyst Detail (Top Flagged)
            st.markdown("---")
            st.subheader("🤖 AI Risk Analyst Deep Dive")
            
            # Selectbox for specific transaction insight
            selected_id = st.selectbox(
                "Select Transaction for AI Explanation",
                options=[t['transaction_id'] for t in txns],
                format_func=lambda x: f"TXN: {x[:8]}... - {next(t['merchant'] for t in txns if t['transaction_id'] == x)}"
            )
            
            if selected_id:
                selected_txn = next(t for t in txns if t['transaction_id'] == selected_id)
                col_exp, col_evid = st.columns([2, 1])
                
                with col_exp:
                    st.info(f"**AI Explanation:**\n\n{selected_txn['explanation']}")
                
                with col_evid:
                    st.warning("**Supporting Evidence:**")
                    for evidence in selected_txn['supporting_evidence']:
                        st.markdown(f"- {evidence}")
            
            # 5. Custom AI Query
            st.markdown("---")
            user_query = st.text_input("Ask AI Analyst about these patterns:", placeholder="e.g. Why is U1's risk increasing?")
            if user_query:
                st.write(f"🔍 *AI analysis for query '{user_query}' would appear here based on RAG context.*")
                st.info("The Risk Analyst is currently monitoring the live stream. Patterns suggest behavioral shifts in periodic spending.")

    else:
        st.error("❌ Unable to connect to FinGuard AI API. Ensure `api_main.py` is running.")
    
    time.sleep(refresh_rate)
    st.rerun()
