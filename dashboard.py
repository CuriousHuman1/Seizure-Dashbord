import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime

# --- CONFIGURATION ---
FIREBASE_URL = "https://seizure-detection-1465a-default-rtdb.firebaseio.com/live_vitals.json"

st.set_page_config(page_title="Live Patient Vitals", page_icon="🫀", layout="wide")

st.title("🫀 Patient Vitals Monitoring Dashboard")
st.markdown("Live telemetry from wearable seizure detection system.")

# --- STATIC UI ELEMENTS (Only drawn once) ---
# We create empty placeholders. We will inject data into these 4 times a second 
# without refreshing the rest of the page.
metrics_placeholder = st.empty()
st.divider()

st.subheader("📈 Heart Rate Trend")
hr_placeholder = st.empty()

st.subheader("🩸 SpO2 Trend")
spo2_placeholder = st.empty()

st.subheader("📳 Motion Magnitude (m/s²)")
motion_placeholder = st.empty()

caption_placeholder = st.empty()

def fetch_data():
    """Fetches the latest data from Firebase"""
    try:
        # Fetching the last 100 records (At 4 Hz, 20 seconds = 80 records, so 100 is safe)
        url = f'{FIREBASE_URL}?orderBy="$key"&limitToLast=100'
        response = requests.get(url)
        
        if response.status_code == 200 and response.json() is not None:
            data = response.json()
            
            df = pd.DataFrame.from_dict(data, orient='index')
            df['time'] = pd.to_datetime(df['time'], unit='s', utc=True).dt.tz_convert('Asia/Kolkata')
            df.set_index('time', inplace=True)
            
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame()

# --- MAIN LOOP (Updates in-place) ---
while True:
    df = fetch_data()
    
    if not df.empty:
        # --- 20-SECOND ZOOM LOGIC ---
        # Find the latest timestamp in the data and filter out anything older than 20 seconds
        max_time = df.index.max()
        start_time = max_time - pd.Timedelta(seconds=20)
        df_20s = df[df.index >= start_time]

        # Ensure we have data in the 20s window before drawing
        if not df_20s.empty:
            latest_hr = df_20s['hr'].iloc[-1]
            latest_spo2 = df_20s['spo2'].iloc[-1]
            latest_motion = df_20s['motion'].iloc[-1]
            
            # 1. Update Metrics
            with metrics_placeholder.container():
                col1, col2, col3 = st.columns(3)
                spo2_delta = "CRITICAL LOW!" if 0 < latest_spo2 < 90 else "Normal"
                spo2_color = "inverse" if 0 < latest_spo2 < 90 else "normal"
                
                col1.metric("Heart Rate", f"{latest_hr:.0f} BPM")
                col2.metric("SpO2 Levels", f"{latest_spo2:.0f} %", delta=spo2_delta, delta_color=spo2_color)
                col3.metric("Motion Magnitude", f"{latest_motion:.2f} m/s²")
            
            # 2. Update Graphs (Injecting directly into placeholders)
            hr_placeholder.line_chart(df_20s[['hr']], color="#ff4b4b")
            spo2_placeholder.line_chart(df_20s[['spo2']], color="#0099ff")
            motion_placeholder.line_chart(df_20s[['motion']], color="#ffaa00")
            
            caption_placeholder.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S.%f')[:-4]}")
            
    else:
        metrics_placeholder.warning("⏳ Waiting for data from the ESP32 Wearable...")

    # Sleep for 0.25 seconds (4 times per second updates)
    time.sleep(2)
