import streamlit as st
import pandas as pd
import sqlite3
import plotly.graph_objects as go
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Global Fleet Command", layout="wide")
st.title("🚢 AGV GLOBAL | LOGISTICS CONTROL TOWER")
st.write(f"Systems Update: {datetime.now().strftime('%Y-%m-%d %H:%M')} WAT")

# 2. THE CLEAN REBUILD: Database Initialization
def rebuild_logistics_system():
    # Using a fresh connection
    conn = sqlite3.connect('logistics_master.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Drop and Recreate to ensure a clean sheet
    cursor.execute('DROP TABLE IF EXISTS GlobalShipments')
    cursor.execute('''
    CREATE TABLE GlobalShipments (
        ShipID INTEGER PRIMARY KEY,
        ShipName TEXT,
        Origin TEXT,
        Destination TEXT,
        Lat REAL,
        Lon REAL,
        Status TEXT,
        Weather TEXT,
        RiskLevel TEXT
    )
    ''')

    # The Expanded 8-Ship Fleet
    fleet = [
        (1, 'Maersk Advancer', 'Shanghai', 'Lagos (Apapa)', 6.45, 3.39, 'Moving', 'Clear', 'Low'),
        (2, 'MSC Carole', 'Singapore', 'Lekki Deep Sea Port', 6.41, 3.93, 'Moving', 'Clear', 'Low'),
        (3, 'Ever Given II', 'Singapore', 'Rotterdam', 29.97, 32.53, 'Stationary', 'High Winds', 'High'),
        (4, 'CMA CGM Liberty', 'Marseille', 'Lagos (Tin Can)', 6.44, 3.35, 'Moving', 'Clear', 'Low'),
        (5, 'HMM Rotterdam', 'Busan', 'Lagos (Apapa)', 35.17, 129.07, 'Moving', 'Foggy', 'Low'),
        (6, 'ZIM Luanda', 'Haifa', 'Luanda', -8.81, 13.23, 'Moving', 'Clear', 'Low'),
        (7, 'COSCO Pride', 'Ningbo', 'Onne Port', 4.67, 7.15, 'Stationary', 'Stormy', 'High'),
        (8, 'Grimaldi Great Lagos', 'Antwerp', 'Lagos', 51.21, 4.40, 'Moving', 'Clear', 'Low')
    ]
    
    cursor.executemany('''
        INSERT INTO GlobalShipments (ShipID, ShipName, Origin, Destination, Lat, Lon, Status, Weather, RiskLevel)
        VALUES (?,?,?,?,?,?,?,?,?)
    ''', fleet)
    conn.commit()
    return conn

# Connect to the clean sheet
if 'log_conn' not in st.session_state:
    st.session_state.log_conn = rebuild_logistics_system()

# 3. INTERACTIVE RISK AUDIT
st.sidebar.header("🕹️ Command Simulation")
selected_ship = st.sidebar.selectbox("Vessel Select", pd.read_sql_query("SELECT ShipName FROM GlobalShipments", st.session_state.log_conn))

if st.sidebar.button("🚨 Simulate Engine Failure"):
    cursor = st.session_state.log_conn.cursor()
    cursor.execute("UPDATE GlobalShipments SET Status = 'Stationary', RiskLevel = 'CRITICAL' WHERE ShipName = ?", (selected_ship,))
    st.session_state.log_conn.commit()
    st.sidebar.error(f"EMERGENCY: {selected_ship} reports zero knots.")

# 4. DATA VISUALIZATION
df = pd.read_sql_query("SELECT * FROM GlobalShipments", st.session_state.log_conn)

# Refined Risk Calculation for the Dashboard
def refine_risk(row):
    if row['Status'] == 'Stationary' and row['Weather'] != 'Clear':
        return "MODERATE (Weather)"
    if row['Status'] == 'Stationary' and row['Weather'] == 'Clear':
        return "CRITICAL (Unknown)"
    return "NOMINAL"

df['Audit_Status'] = df.apply(refine_risk, axis=1)

# The Map
fig = go.Figure(go.Scattergeo(
    lat = df['Lat'], lon = df['Lon'],
    mode = 'markers+text',
    text = df['ShipName'],
    textposition = "top center",
    marker = dict(
        size = 12,
        color = df['Audit_Status'].map({'NOMINAL': 'green', 'MODERATE (Weather)': 'orange', 'CRITICAL (Unknown)': 'red'}),
        symbol = 'diamond',
        line = dict(width=1, color='white')
    )
))

fig.update_layout(
    geo = dict(projection_type='equirectangular', showland=True, landcolor="rgb(240, 240, 240)", oceancolor="rgb(10, 25, 50)", showocean=True),
    margin={"r":0,"t":0,"l":0,"b":0}, height=500, template="plotly_dark"
)
st.plotly_chart(fig, use_container_width=True)

# 5. FLEET SUMMARY TABLE
st.subheader("📋 Fleet Audit Log")
st.dataframe(df[['ShipName', 'Origin', 'Destination', 'Status', 'Weather', 'Audit_Status']], use_container_width=True)

# AI Prescriptive Report
if "CRITICAL" in df[df['ShipName'] == selected_ship]['Audit_Status'].values:
    st.error(f"**ACTION REQUIRED FOR {selected_ship.upper()}:** Vessel is stationary in clear weather. Initiate mechanical audit and notify {df[df['ShipName'] == selected_ship]['Destination'].values[0]} port authorities.")
