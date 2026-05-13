import streamlit as st
import pandas as pd
import sqlite3
import requests
import plotly.express as px
from datetime import datetime

# 1. Page Config
st.set_page_config(page_title="AGV Treasury Command", layout="wide")

st.title("🏢 AGV GROUP | AUTOMATED TREASURY & FX HEDGE")
st.write("Multi-subsidiary risk management engine with live USD/NGN market triggers.")

# 2. Database Engine (AGV Production Architecture)
def init_treasury_db():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE Subsidiaries (SubID INT, Name TEXT, HedgeThreshold REAL)')
    cursor.execute('CREATE TABLE Treasury (SubID INT, NGN_Balance REAL, USD_Balance REAL)')
    cursor.execute('CREATE TABLE Hedge_Logs (LogID INTEGER PRIMARY KEY, Timestamp TEXT, Subsidiary TEXT, Action TEXT, Amount_NGN REAL)')
    
    # Seeding your exact Tiered Capital Allocation
    subs = [(1, 'AGV Media Hub', 1.0), (2, 'AGV Systems Engineering', 2.5), (3, 'AGV Heritage Logistics', 5.0)]
    cash = [(1, 45000000.0, 0.0), (2, 15000000.0, 0.0), (3, 5000000.0, 0.0)]
    
    cursor.executemany("INSERT INTO Subsidiaries VALUES (?,?,?)", subs)
    cursor.executemany("INSERT INTO Treasury VALUES (?,?,?)", cash)
    conn.commit()
    return conn

if 'fin_conn' not in st.session_state:
    st.session_state.fin_conn = init_treasury_db()

# 3. Live Market Data (The Ping)
st.sidebar.header("📡 Market Feed")
opening_rate = 1450.00
try:
    response = requests.get("https://open.er-api.com/v6/latest/USD")
    live_rate = response.json()['rates']['NGN']
    market_move = ((live_rate - opening_rate) / opening_rate) * 100
    st.sidebar.metric("USD/NGN Rate", f"₦{live_rate:,.2f}", f"{market_move:.2f}%")
except:
    live_rate = 1500.00
    market_move = 3.45 # Fallback for demo
    st.sidebar.warning("Using Offline Baseline Rate")

# 4. Execution Logic (The 'Trade' Trigger)
if st.sidebar.button("⚡ Execute Automated Hedge"):
    cursor = st.session_state.fin_conn.cursor()
    cursor.execute("SELECT s.SubID, s.Name, s.HedgeThreshold, t.NGN_Balance, t.USD_Balance FROM Subsidiaries s JOIN Treasury t ON s.SubID = t.SubID")
    units = cursor.fetchall()
    
    for sub_id, name, threshold, ngn_bal, usd_bal in units:
        if abs(market_move) >= threshold:
            hedge_ngn = ngn_bal * 0.15
            new_ngn = ngn_bal - hedge_ngn
            new_usd = usd_bal + (hedge_ngn / live_rate)
            
            cursor.execute("UPDATE Treasury SET NGN_Balance = ?, USD_Balance = ? WHERE SubID = ?", (new_ngn, new_usd, sub_id))
            cursor.execute("INSERT INTO Hedge_Logs (Timestamp, Subsidiary, Action, Amount_NGN) VALUES (?,?,?,?)",
                           (datetime.now().strftime("%H:%M:%S"), name, 'AUTO-HEDGE', hedge_ngn))
    st.session_state.fin_conn.commit()
    st.success(f"Hedge Protocol Executed at {market_move:.2f}% Volatility.")

# 5. Visualizing the Impact
df = pd.read_sql_query("SELECT s.Name, t.NGN_Balance, t.USD_Balance FROM Subsidiaries s JOIN Treasury t ON s.SubID = t.SubID", st.session_state.fin_conn)
logs_df = pd.read_sql_query("SELECT * FROM Hedge_Logs ORDER BY LogID DESC", st.session_state.fin_conn)

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Group Asset Distribution (USD Assets)")
    fig = px.bar(df, x='Name', y='USD_Balance', color='Name', template="plotly_dark", height=400)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Consolidated Balances")
    st.dataframe(df[['Name', 'NGN_Balance', 'USD_Balance']], use_container_width=True)

# 6. Audit Trail
st.divider()
st.subheader("📋 Official AGV Group Audit Log")
st.table(logs_df)
