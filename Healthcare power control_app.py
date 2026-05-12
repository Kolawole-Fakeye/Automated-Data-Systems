import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3

# 1. Page Configuration
st.set_page_config(page_title="St. Jude's Power Command", layout="wide")

st.title("🏥 ST. JUDE'S | BIOMEDICAL INFRASTRUCTURE COMMAND")
st.write("Live monitoring of Hospital Power Zones, Load Shedding, and Hybrid Source Health.")

# 2. Database Initialization (Using your exact architecture)
def init_db():
    conn = sqlite3.connect(':memory:') # Fresh state for the web app
    cursor = conn.cursor()
    
    # Hospital Zones
    cursor.execute('CREATE TABLE Hospital_Zones (ZoneID INT, ZoneName TEXT, Criticality TEXT)')
    zones = [(1, 'ICU & Operating Theaters', 'LIFE-SUPPORT'),
             (2, 'MRI & Radiology Wing', 'DIAGNOSTIC'),
             (3, 'Admin & General Services', 'NON-ESSENTIAL')]
    cursor.executemany("INSERT INTO Hospital_Zones VALUES (?,?,?)", zones)
    
    # Power Sources
    cursor.execute('CREATE TABLE Power_Sources (SourceID INT, SourceName TEXT, CurrentVoltage REAL, Fuel_or_Charge REAL, Is_Active INT)')
    sources = [(1, 'Public Grid', 230.0, 100.0, 1),
               (2, 'Solar/Battery Bank', 230.0, 85.0, 0),
               (3, 'Emergency Diesel Gen', 0.0, 100.0, 0)]
    cursor.executemany("INSERT INTO Power_Sources VALUES (?,?,?,?,?)", sources)
    
    return conn

if 'conn' not in st.session_state:
    st.session_state.conn = init_db()

# 3. Interactive Simulation: Grid Collapse
st.sidebar.header("🕹️ Simulation Control")
if st.sidebar.button("🚨 Simulate Grid Collapse"):
    cursor = st.session_state.conn.cursor()
    # Step A: Drop Grid Voltage
    cursor.execute("UPDATE Power_Sources SET CurrentVoltage = 160.0, Is_Active = 0 WHERE SourceName = 'Public Grid'")
    # Step B: Engage Solar/Gen for ICU
    cursor.execute("UPDATE Power_Sources SET Is_Active = 1 WHERE SourceName = 'Solar/Battery Bank'")
    cursor.execute("UPDATE Power_Sources SET CurrentVoltage = 230.0, Is_Active = 1 WHERE SourceName = 'Emergency Diesel Gen'")
    st.sidebar.error("GRID COLLAPSE DETECTED: Emergency Protocol Active.")
else:
    st.sidebar.success("Grid Healthy (230V stable)")

# 4. Fetch Data for Dashboard
df_sources = pd.read_sql_query("SELECT * FROM Power_Sources", st.session_state.conn)
loads = {'ICU': 150, 'Imaging': 100, 'Admin': 0 if df_sources.loc[0, 'Is_Active'] == 0 else 20}

# 5. The Modern Dashboard (Your Exact Layout)
fig = make_subplots(
    rows=2, cols=3,
    specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
           [{"type": "bar", "colspan": 3}, None, None]],
    vertical_spacing=0.15,
    subplot_titles=("Grid Health (V)", "Solar Battery %", "Gen Fuel %", "Live Load Distribution by Zone (kW)")
)

# Grid Gauge
fig.add_trace(go.Indicator(
    mode = "gauge+number", value = df_sources.loc[0, 'CurrentVoltage'],
    gauge = {'axis': {'range': [0, 250]}, 'bar': {'color': "#636EFA"}}
), row=1, col=1)

# Solar Gauge
fig.add_trace(go.Indicator(
    mode = "gauge+number", value = df_sources.loc[1, 'Fuel_or_Charge'],
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00CC96"}}
), row=1, col=2)

# Gen Gauge
fig.add_trace(go.Indicator(
    mode = "gauge+number", value = df_sources.loc[2, 'Fuel_or_Charge'],
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#EF553B"}}
), row=1, col=3)

# Load Bar
fig.add_trace(go.Bar(
    x=list(loads.keys()), y=list(loads.values()),
    marker_color=['#FF4B4B', '#FACC15', '#4B4B4B'],
    text=list(loads.values()), textposition='auto',
), row=2, col=1)

fig.update_layout(template="plotly_dark", height=700, paper_bgcolor="black", plot_bgcolor="black")
st.plotly_chart(fig, use_container_width=True)

# 6. Critical Status Logs
st.subheader("📋 System Logs")
if df_sources.loc[0, 'CurrentVoltage'] < 200:
    st.warning("⚠️ Critical Under-Voltage on Main Grid. Admin Wing (Zone 3) has been SHEDDED.")
else:
    st.info("System healthy. Admin Wing (Zone 3) connected.")
