import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
# Your specific Firebase Realtime Database URL
FIREBASE_URL = "https://seizure-detection-1465a-default-rtdb.firebaseio.com/live_vitals.json"

st.set_page_config(page_title="Live Patient Vitals", page_icon="🫀", layout="wide")

st.title("🫀 Patient Vitals Monitoring Dashboard")
st.markdown("Live telemetry from wearable seizure detection system.")

# Placeholder to allow complete UI refreshing
dashboard_placeholder = st.empty()

def fetch_data():
    """Fetches the latest 60 sensor readings from Firebase"""
    try:
        # We use Firebase REST API to get only the latest 60 records to keep it fast
        url = f'{FIREBASE_URL}?orderBy="$key"&limitToLast=60'
        response = requests.get(url)
        
        if response.status_code == 200 and response.json() is not None:
            data = response.json()
            
            # Convert Firebase dictionary into a Pandas DataFrame
            df = pd.DataFrame.from_dict(data, orient='index')
            
            # Convert Unix timestamp to readable DateTime (Indian Standard Time)
            df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert('Asia/Kolkata')
            df.set_index('time', inplace=True)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- MAIN LOOP ---
while True:
    df = fetch_data()
    
    with dashboard_placeholder.container():
        if not df.empty:
            # Extract the very latest reading for the metric cards
            latest_hr = df['hr'].iloc[-1]
            latest_spo2 = df['spo2'].iloc[-1]
            latest_motion = df['motion'].iloc[-1]
            
            # --- TOP ROW: METRIC CARDS ---
            col1, col2, col3 = st.columns(3)
            
            # Highlight SpO2 in red if it drops below 90%
            spo2_delta = "CRITICAL LOW!" if latest_spo2 > 0 and latest_spo2 < 90 else "Normal"
            spo2_color = "inverse" if latest_spo2 > 0 and latest_spo2 < 90 else "normal"
            
            col1.metric("Heart Rate", f"{latest_hr:.0f} BPM")
            col2.metric("SpO2 Levels", f"{latest_spo2:.0f} %", delta=spo2_delta, delta_color=spo2_color)
            col3.metric("Motion Magnitude", f"{latest_motion:.2f} m/s²")
            
            st.divider()
            
            # --- GRAPHS ---
            st.subheader("📈 Heart Rate Trend")
            st.line_chart(df[['hr']], color="#ff4b4b")
            
            st.subheader("🩸 SpO2 Trend")
            st.line_chart(df[['spo2']], color="#0099ff")
            
            st.subheader("📳 Motion Magnitude (m/s²)")
            st.area_chart(df[['motion']], color="#ffaa00")
            
            st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")
            
        else:
            st.warning("⏳ Waiting for data from the ESP32 Wearable... Please ensure the device is connected to Wi-Fi.")

    # Pause execution for 5 seconds, then Streamlit automatically updates the loop
    time.sleep(5)
    st.rerun()