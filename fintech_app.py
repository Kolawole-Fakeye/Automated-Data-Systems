import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Setup the Web Page
st.set_page_config(page_title="Fintech Risk Engine", layout="wide")

st.title("📈 Fintech Hedging & Currency Risk Engine")
st.write("Automated FX volatility assessment and hedging simulation for multi-currency operations.")

# 2. Simulated Currency Data (The "Intelligence" Layer)
def get_fintech_data():
    data = {
        'Currency': ['USD/NGN', 'EUR/NGN', 'GBP/NGN', 'CNY/NGN'],
        'Current_Rate': [1450.00, 1570.00, 1820.00, 200.00],
        'Volatility_Index': [12.5, 8.2, 9.1, 5.4],
        'Exposure_Amount': [50000, 25000, 15000, 100000]
    }
    df = pd.DataFrame(data)
    # Calculate Risk Value (Exposure * Volatility)
    df['Risk_Value_NGN'] = (df['Exposure_Amount'] * df['Current_Rate'] * (df['Volatility_Index']/100))
    return df

df = get_fintech_data()

# 3. Visualization: Risk Distribution
st.subheader("Financial Exposure Analysis")
col1, col2 = st.columns(2)

with col1:
    fig_pie = px.pie(df, values='Exposure_Amount', names='Currency', 
                     title="Portfolio Exposure by Currency",
                     hole=0.4, template="plotly_dark")
    st.plotly_chart(fig_pie, use_container_width=True)

with col2:
    fig_bar = px.bar(df, x='Currency', y='Risk_Value_NGN', 
                     title="Estimated Risk Value (NGN)",
                     color='Currency', template="plotly_dark")
    st.plotly_chart(fig_bar, use_container_width=True)

# 4. The "Hedging" Calculator (Interactive Feature)
st.divider()
st.subheader("🛡️ Hedging Simulator")
hedge_ratio = st.slider("Select Hedge Percentage (%)", 0, 100, 50)

df['Hedged_Exposure'] = df['Risk_Value_NGN'] * (1 - (hedge_ratio / 100))
st.write(f"By hedging **{hedge_ratio}%** of your portfolio, your unhedged risk drops to:")
st.dataframe(df[['Currency', 'Risk_Value_NGN', 'Hedged_Exposure']])
