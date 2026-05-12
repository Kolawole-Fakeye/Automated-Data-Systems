import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3

# 1. Setup the Web Page
st.set_page_config(page_title="Logistics Hub", layout="wide")

st.title("🌍 Global Logistics Intelligence Hub")
st.write("Real-time maritime asset tracking and operational risk monitoring.")

# 2. Database Logic - Creating a fresh, clean dataset
def get_clean_data():
    # Using ':memory:' for the demo ensures it works perfectly on the Streamlit server
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE Ship_Tracking (
            ShipID INTEGER PRIMARY KEY, 
            ShipName TEXT, 
            CurrentLat REAL, 
            CurrentLon REAL, 
            Status TEXT
        )
    ''')
    
    # Inserting 4 clean rows of data
    ships = [
        (1, 'Everest Carrier', 6.45, 3.38, 'In Transit'),
        (2, 'Oceanic Titan', -22.90, -43.17, 'Moored'),
        (3, 'Sahara Express', 12.00, 15.00, 'Under Maintenance'),
        (4, 'Atlantic Star', 40.71, -74.00, 'In Transit')
    ]
    cursor.executemany('INSERT INTO Ship_Tracking VALUES (?, ?, ?, ?, ?)', ships)
    
    df = pd.read_sql_query("SELECT * FROM Ship_Tracking", conn)
    conn.close()
    return df

# Load the data
df = get_clean_data()

# 3. Visualization Logic - Simplified to avoid Plotly validation errors
fig = go.Figure(go.Scattergeo(
    lat = df['CurrentLat'],
    lon = df['CurrentLon'],
    text = df['ShipName'],
    mode = 'markers',
    marker = dict(
        size = 12,
        color = 'red',
        opacity = 0.8
    )
))

fig.update_layout(
    geo = dict(
        scope='world',
        showland=True,
        landcolor="rgb(240, 240, 240)",
        showocean=True,
        oceancolor="rgb(10, 20, 30)"
    ),
    margin={"r":0,"t":50,"l":0,"b":0},
    template="plotly_dark",
    height=600
)

# 4. Display to the Web
st.plotly_chart(fig, use_container_width=True)

# 5. Display the Data Table for the Recruiter
st.subheader("📋 Fleet Operational Status")
st.dataframe(df, use_container_width=True)
