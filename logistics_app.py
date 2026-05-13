import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# 1. Page Configuration
st.set_page_config(page_title="Titan Fleet Intel", layout="wide")
st.title("🌐 TITAN FLEET INTELLIGENCE | GLOBAL COMMAND")

# 2. THE CLEAN REBUILD: Database Initialization
def rebuild_titan_system():
    conn = sqlite3.connect('titan_fleet.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('DROP TABLE IF EXISTS Fleet')
    cursor.execute('''
    CREATE TABLE Fleet (
        ShipID INTEGER PRIMARY KEY,
        ShipName TEXT,
        Origin TEXT,
        Destination TEXT,
        Lat REAL, Lon REAL,
        Speed REAL, -- 0 means stuck
        Weather TEXT,
        CO2_Metric REAL -- Environmental Impact (Tonnes)
    )
    ''')

    # Modern 8-Ship Fleet
    fleet = [
        (1, 'Maersk Advancer', 'Shanghai', 'Lagos (Apapa)', 6.45, 3.39, 18.5, 'Clear', 124.5),
        (2, 'MSC Carole', 'Singapore', 'Lekki Deep Sea', 6.41, 3.93, 14.2, 'Clear', 98.2),
        (3, 'Ever Given II', 'Singapore', 'Rotterdam', 29.97, 32.53, 0.0, 'High Winds', 0.0),
        (4, 'CMA CGM Liberty', 'Marseille', 'Lagos (Tin Can)', 12.44, -17.35, 16.1, 'Clear', 110.4),
        (5, 'HMM Rotterdam', 'Busan', 'Lagos (Apapa)', 35.17, 129.07, 19.8, 'Foggy', 156.7),
        (6, 'ZIM Luanda', 'Haifa', 'Luanda', -8.81, 13.23, 15.0, 'Clear', 89.1),
        (7, 'COSCO Pride', 'Ningbo', 'Onne Port', 4.67, 7.15, 0.0, 'Stormy', 0.0),
        (8, 'Grimaldi Lagos', 'Antwerp', 'Lagos', 51.21, 4.40, 12.5, 'Clear', 75.3)
    ]
    
    cursor.executemany('INSERT INTO Fleet VALUES (?,?,?,?,?,?,?,?,?)', fleet)
    conn.commit()
    return conn

if 'titan_conn' not in st.session_state:
    st.session_state.titan_conn = rebuild_titan_system()

# 3. TOP KPI ROW (Visibility on what's stuck)
df = pd.read_sql_query("SELECT * FROM Fleet", st.session_state.titan_conn)
stuck_count = len(df[df['Speed'] == 0])
total_co2 = df['CO2_Metric'].sum()

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Fleet Utilization", f"{len(df) - stuck_count}/{len(df)} Active", f"-{stuck_count} Stationary", delta_color="inverse")
kpi2.metric("Fleet Status", "CRITICAL" if stuck_count > 1 else "STABLE")
kpi3.metric("Daily CO2 Impact", f"{total_co2:.1f} T", "Eco-Track Active")

# 4. MODERN HIGH-CONTRAST MAP
st.subheader("🛰️ Global Motion Tracking")
# We use color to show speed (Moving vs Stuck) and size to show CO2 impact
fig = px.scatter_geo(df,
                     lat='Lat', lon='Lon',
                     color='Speed', # Visual cue for motion
                     size='CO2_Metric', # Visual cue for environmental impact
                     hover_name='ShipName',
                     hover_data=['Destination', 'Weather', 'Speed'],
                     projection="natural earth",
                     color_continuous_scale=px.colors.sequential.Viridis,
                     template="plotly_dark")

fig.update_layout(height=600, margin={"r":0,"t":40,"l":0,"b":0})
st.plotly_chart(fig, use_container_width=True)

# 5. SPLIT VIEW: DATA AUDIT & ENVIRONMENTAL IMPACT
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📋 Fleet Motion Audit")
    # Styling to highlight stuck ships in red
    def highlight_stuck(s):
        return ['background-color: #990000' if v == 0 else '' for v in s]
    
    st.dataframe(df[['ShipName', 'Destination', 'Speed', 'Weather']].style.apply(highlight_stuck, subset=['Speed']), use_container_width=True)

with col2:
    st.subheader("🌱 Environmental Impact")
    fig_co2 = px.pie(df, values='CO2_Metric', names='ShipName', hole=0.4, 
                     color_discrete_sequence=px.colors.sequential.Greens_r,
                     template="plotly_dark")
    st.plotly_chart(fig_co2, use_container_width=True)
