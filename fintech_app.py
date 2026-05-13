import streamlit as st
import pandas as pd
import sqlite3
import requests
import plotly.express as px
from datetime import datetime

# ====================== CONFIG ======================
st.set_page_config(
    page_title="AGV Treasury Command",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Luxurious Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0a0a0a; }
    h1, h2 { color: #ffd700; font-weight: 600; }
    .stMetric { background-color: #1a1a1a; border-radius: 12px; padding: 10px; }
    .sidebar .sidebar-content { background-color: #111111; }
    </style>
""", unsafe_allow_html=True)

st.title("💰 AGV GROUP TREASURY COMMAND CENTER")
st.markdown("**Real-time Currency Risk Management & Automated Hedging System**")

# ====================== DATABASE ======================
def init_db():
    conn = sqlite3.connect('agv_treasury.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS Subsidiaries 
                      (SubID INT PRIMARY KEY, Name TEXT, HedgeThreshold REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Treasury 
                      (SubID INT PRIMARY KEY, NGN_Balance REAL, USD_Balance REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS Hedge_Logs 
                      (LogID INTEGER PRIMARY KEY, Timestamp TEXT, Subsidiary TEXT, 
                       Action TEXT, Amount_NGN REAL)''')
    
    cursor.execute("SELECT COUNT(*) FROM Subsidiaries")
    if cursor.fetchone()[0] == 0:
        subs = [(1, 'AGV Media Hub', 1.0), (2, 'AGV Systems Engineering', 2.5), (3, 'AGV Heritage Logistics', 5.0)]
        cash = [(1, 45000000.0, 0.0), (2, 15000000.0, 0.0), (3, 5000000.0, 0.0)]
        cursor.executemany("INSERT INTO Subsidiaries VALUES (?,?,?)", subs)
        cursor.executemany("INSERT INTO Treasury VALUES (?,?,?)", cash)
        conn.commit()
    return conn

conn = init_db()

# ====================== LIVE DATA ======================
opening_rate = 1450.00
try:
    response = requests.get("https://open.er-api.com/v6/latest/USD")
    live_rate = response.json()['rates']['NGN']
    market_move = ((live_rate - opening_rate) / opening_rate) * 100
except:
    live_rate, market_move = 1550.00, 6.90

# ====================== KPI SECTION ======================
col1, col2, col3 = st.columns(3)
col1.metric("LIVE USD/NGN", f"₦{live_rate:,.2f}", f"{market_move:+.2f}%")
col2.metric("MARKET STATUS", "HIGH VOLATILITY" if abs(market_move) > 2 else "STABLE")
col3.metric("BASELINE RATE", f"₦{opening_rate:,.2f}")

st.divider()

# ====================== SIDEBAR ======================
st.sidebar.header("⚙️ Simulation Controls")
sim_move = st.sidebar.slider("Simulated Market Volatility (%)", 0.0, 15.0, float(abs(market_move)), step=0.1)

if st.sidebar.button("🚀 RUN TREASURY AUDIT & AUTO-HEDGE", type="primary", use_container_width=True):
    cursor = conn.cursor()
    cursor.execute("""SELECT s.SubID, s.Name, s.HedgeThreshold, t.NGN_Balance, t.USD_Balance 
                      FROM Subsidiaries s JOIN Treasury t ON s.SubID = t.SubID""")
    
    for sub_id, name, threshold, ngn_bal, usd_bal in cursor.fetchall():
        if sim_move >= threshold:
            hedge_ngn = ngn_bal * 0.15
            new_ngn = ngn_bal - hedge_ngn
            new_usd = usd_bal + (hedge_ngn / live_rate)
            
            cursor.execute("UPDATE Treasury SET NGN_Balance = ?, USD_Balance = ? WHERE SubID = ?", 
                           (new_ngn, new_usd, sub_id))
            cursor.execute("""INSERT INTO Hedge_Logs (Timestamp, Subsidiary, Action, Amount_NGN) 
                              VALUES (?,?,?,?)""", 
                           (datetime.now().strftime("%H:%M:%S"), name, 'AUTO-HEDGE', hedge_ngn))
    
    conn.commit()
    st.success("✅ Treasury Audit Completed. Hedges Executed Successfully.")

# ====================== MAIN DASHBOARD ======================
df = pd.read_sql_query("SELECT s.Name, t.NGN_Balance, t.USD_Balance FROM Subsidiaries s JOIN Treasury t ON s.SubID = t.SubID", conn)
logs_df = pd.read_sql_query("SELECT * FROM Hedge_Logs ORDER BY LogID DESC LIMIT 10", conn)

tab1, tab2 = st.tabs(["📊 Consolidated Treasury View", "📜 Recent Audit Trail"])

with tab1:
    st.subheader("Subsidiary Treasury Position")
    fig = px.bar(df, x='Name', y=['NGN_Balance', 'USD_Balance'],
                 title="Group Treasury Balances (NGN & USD)",
                 barmode='group',
                 template="plotly_dark",
                 height=520,
                 color_discrete_map={'NGN_Balance': '#00CC96', 'USD_Balance': '#636EFA'})
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Recent Hedge Actions")
    st.dataframe(logs_df.style.format({"Amount_NGN": "₦{:,.2f}"}), use_container_width=True)

st.caption("Automated Treasury Command System | Built by Kolawole Fakeye • Data Analyst & Technical Specialist")
