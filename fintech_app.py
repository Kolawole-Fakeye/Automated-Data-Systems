import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="AGV Treasury Command", layout="wide")

st.title("🏢 AGV GROUP | TREASURY COMMAND CENTER")
st.write("Automated FX Risk Mitigation & Capital Allocation.")

# 2. Database Logic (The "Stable" Way)
def get_db_connection():
    # Using a local file instead of :memory: for better stability during clicks
    conn = sqlite3.connect('agv_internal.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS Subsidiaries (SubID INT PRIMARY KEY, Name TEXT, HedgeThreshold REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Treasury (SubID INT PRIMARY KEY, NGN_Balance REAL, USD_Balance REAL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Hedge_Logs (LogID INTEGER PRIMARY KEY, Timestamp TEXT, Subsidiary TEXT, Action TEXT, Amount_NGN REAL)')
    
    # Check if seeded
    cursor.execute("SELECT COUNT(*) FROM Subsidiaries")
    if cursor.fetchone()[0] == 0:
        subs = [(1, 'AGV Media Hub', 1.0), (2, 'AGV Systems Engineering', 2.5), (3, 'AGV Heritage Logistics', 5.0)]
        cash = [(1, 45000000.0, 0.0), (2, 15000000.0, 0.0), (3, 5000000.0, 0.0)]
        cursor.executemany("INSERT INTO Subsidiaries VALUES (?,?,?)", subs)
        cursor.executemany("INSERT INTO Treasury VALUES (?,?,?)", cash)
    conn.commit()
    return conn

conn = init_db()

# 3. Interactive Sidebar (The "What-If" Simulator)
st.sidebar.header("🕹️ Market Simulator")
st.sidebar.info("Adjust the slider to simulate a Naira devaluation and trigger the auto-hedge.")
simulated_move = st.sidebar.slider("Simulated Market Volatility (%)", 0.0, 10.0, 0.0, step=0.1)

# 4. The Execution Engine
if st.sidebar.button("⚡ Run Treasury Audit"):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.SubID, s.Name, s.HedgeThreshold, t.NGN_Balance, t.USD_Balance 
        FROM Subsidiaries s JOIN Treasury t ON s.SubID = t.SubID
    """)
    units = cursor.fetchall()
    
    for sub_id, name, threshold, ngn_bal, usd_bal in units:
        if simulated_move >= threshold:
            # Logic: Hedge 15% of NGN
            hedge_ngn = ngn_bal * 0.15
            new_ngn = ngn_bal - hedge_ngn
            new_usd = usd_bal + (hedge_ngn / 1500) # Using 1500 as baseline
            
            cursor.execute("UPDATE Treasury SET NGN_Balance = ?, USD_Balance = ? WHERE SubID = ?", (new_ngn, new_usd, sub_id))
            cursor.execute("INSERT INTO Hedge_Logs (Timestamp, Subsidiary, Action, Amount_NGN) VALUES (?,?,?,?)",
                           (datetime.now().strftime("%H:%M:%S"), name, 'AUTO-HEDGE', hedge_ngn))
    conn.commit()
    st.sidebar.success(f"Audit Complete. Market move of {simulated_move}% processed.")

# 5. Visual Dashboard
df = pd.read_sql_query("SELECT s.Name, t.NGN_Balance, t.USD_Balance FROM Subsidiaries s JOIN Treasury t ON s.SubID = t.SubID", conn)
logs_df = pd.read_sql_query("SELECT * FROM Hedge_Logs ORDER BY LogID DESC LIMIT 5", conn)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("USD Capital Reserves")
    fig = px.bar(df, x='Name', y='USD_Balance', color='Name', 
                 color_discrete_sequence=px.colors.qualitative.Pastel,
                 template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Current Group Balances")
    st.dataframe(df.style.format({"NGN_Balance": "{:,.2f}", "USD_Balance": "{:,.2f}"}), use_container_width=True)

# 6. Audit Trail
st.subheader("📋 Recent Treasury Actions")
if not logs_df.empty:
    st.table(logs_df)
else:
    st.write("No hedge actions triggered yet. Increase volatility to test.")
