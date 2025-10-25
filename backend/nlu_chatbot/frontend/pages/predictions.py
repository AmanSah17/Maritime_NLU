"""
Maritime Vessel Trajectory Predictions
Uses XGBoost model predictions with parsed query data
"""

import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
import pandas as pd
from auth_manager import AuthManager
from datetime import datetime

st.set_page_config(page_title="Vessel Predictions", layout="wide")

# Custom CSS for defense theme
st.markdown("""
<style>
:root {
    --primary-navy: #001F3F;
    --secondary-gray: #2C3E50;
    --accent-cyan: #00D9FF;
}

body {
    background: linear-gradient(135deg, #001F3F 0%, #2C3E50 100%);
    color: #E8E8E8;
    font-family: 'Courier New', monospace;
}

.stApp {
    background: linear-gradient(135deg, #001F3F 0%, #2C3E50 100%);
}

h1, h2, h3 {
    color: #00D9FF;
    text-shadow: 0 0 10px rgba(0, 217, 255, 0.5);
    letter-spacing: 2px;
}

.prediction-card {
    background: rgba(44, 62, 80, 0.7);
    border: 2px solid #00D9FF;
    border-radius: 4px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 0 10px rgba(0, 217, 255, 0.2);
}

.prediction-header {
    background: linear-gradient(90deg, #001F3F 0%, #2C3E50 50%, #001F3F 100%);
    border: 2px solid #00D9FF;
    border-radius: 4px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Initialize authentication
AuthManager.init_session_state()

# Try to restore from cookies first
if not st.session_state.get("authenticated"):
    AuthManager.restore_from_cookies()

# Check if user is authenticated
if not st.session_state.get("authenticated"):
    st.error("❌ Please login first to access predictions")
    if st.button("Go to Login"):
        st.switch_page("pages/auth.py")
    st.stop()

# Navigation
col1, col2, col3, col4 = st.columns(4)
with col1:
    if st.button("🏠 Home"):
        st.switch_page("app.py")
with col2:
    if st.button("📊 Dashboard"):
        st.switch_page("pages/show_dataframes.py")
with col3:
    if st.button("👤 Admin"):
        st.switch_page("pages/admin_panel.py")
with col4:
    if st.button("🎯 Predictions"):
        st.rerun()

st.markdown('<div class="prediction-header"><h1>🎯 VESSEL TRAJECTORY PREDICTIONS</h1></div>', unsafe_allow_html=True)
st.write("AI-powered vessel position predictions using XGBoost model")

backend_base = "http://127.0.0.1:8000"

# Sidebar: Vessel Selection
with st.sidebar:
    st.markdown("### 🚢 Select Vessel for Prediction")
    
    # Fetch available vessels
    @st.cache_data(ttl=300)
    def fetch_vessels():
        try:
            r = requests.get(f"{backend_base}/vessels", timeout=5)
            return r.json().get("vessels", [])
        except:
            return []
    
    vessels = fetch_vessels()
    
    if vessels:
        selected_vessel = st.selectbox("Choose vessel", options=vessels, key="pred_vessel")
        sequence_length = st.slider("Historical points for prediction", 6, 24, 12)
        
        if st.button("🔮 Predict Trajectory"):
            st.session_state.predict_vessel = selected_vessel
            st.session_state.predict_seq_len = sequence_length
    else:
        st.warning("No vessels available")

# Main content
if "predict_vessel" in st.session_state:
    vessel_name = st.session_state.predict_vessel
    seq_len = st.session_state.predict_seq_len
    
    with st.spinner(f"🔮 Predicting trajectory for {vessel_name}..."):
        try:
            # Call prediction endpoint
            response = requests.post(
                f"{backend_base}/predict/trajectory",
                json={
                    "vessel": vessel_name,
                    "sequence_length": seq_len
                },
                timeout=30
            )
            
            result = response.json()

            if result.get("prediction_available"):
                model_mode = result.get("model_mode", "UNKNOWN")
                if model_mode == "DEMO":
                    st.warning(f"⚠️  DEMO MODE: Using simulated predictions (XGBoost model not loaded)")
                else:
                    st.success(f"✅ Prediction successful for {result['vessel_name']}")
                
                # Display prediction metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current LAT",
                        f"{result['last_known_lat']:.4f}°"
                    )
                
                with col2:
                    st.metric(
                        "Current LON",
                        f"{result['last_known_lon']:.4f}°"
                    )
                
                with col3:
                    st.metric(
                        "Predicted LAT",
                        f"{result['predicted_lat']:.4f}°"
                    )
                
                with col4:
                    st.metric(
                        "Predicted LON",
                        f"{result['predicted_lon']:.4f}°"
                    )
                
                st.markdown("---")
                
                # Display speed and course
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Current SOG",
                        f"{result['last_known_sog']:.2f} knots"
                    )
                
                with col2:
                    st.metric(
                        "Predicted SOG",
                        f"{result['predicted_sog']:.2f} knots"
                    )
                
                with col3:
                    st.metric(
                        "Current COG",
                        f"{result['last_known_cog']:.0f}°"
                    )
                
                with col4:
                    st.metric(
                        "Predicted COG",
                        f"{result['predicted_cog']:.0f}°"
                    )
                
                st.markdown("---")
                
                # Display map with predictions
                st.subheader("🗺️ Prediction Map")
                
                if "map_data" in result:
                    map_data = result["map_data"]
                    
                    # Create map centered on current position
                    current_lat = map_data["current_position"]["lat"]
                    current_lon = map_data["current_position"]["lon"]
                    
                    m = folium.Map(
                        location=[current_lat, current_lon],
                        zoom_start=10,
                        tiles="OpenStreetMap"
                    )
                    
                    # Add current position marker
                    folium.CircleMarker(
                        location=[current_lat, current_lon],
                        radius=10,
                        popup=f"Current Position<br>{result['last_timestamp']}",
                        color="#00CC44",
                        fill=True,
                        fillColor="#00CC44",
                        fillOpacity=0.8,
                        weight=2
                    ).add_to(m)
                    
                    # Add predicted position marker
                    pred_lat = map_data["predicted_position"]["lat"]
                    pred_lon = map_data["predicted_position"]["lon"]
                    
                    folium.CircleMarker(
                        location=[pred_lat, pred_lon],
                        radius=10,
                        popup=f"Predicted Position",
                        color="#00D9FF",
                        fill=True,
                        fillColor="#00D9FF",
                        fillOpacity=0.8,
                        weight=2
                    ).add_to(m)
                    
                    # Draw line between current and predicted
                    folium.PolyLine(
                        locations=[[current_lat, current_lon], [pred_lat, pred_lon]],
                        color="#FF9900",
                        weight=2,
                        opacity=0.7,
                        popup="Predicted trajectory"
                    ).add_to(m)
                    
                    # Add track history
                    if "track" in map_data and map_data["track"]:
                        track_points = [
                            [point["LAT"], point["LON"]]
                            for point in map_data["track"]
                        ]
                        folium.PolyLine(
                            locations=track_points,
                            color="#00D9FF",
                            weight=1,
                            opacity=0.5,
                            popup="Historical track"
                        ).add_to(m)
                    
                    st_folium(m, width=1200, height=600)
                
                # Display metadata
                st.markdown("---")
                st.markdown("**📊 Prediction Metadata**")
                
                metadata_col1, metadata_col2 = st.columns(2)
                
                with metadata_col1:
                    st.info(f"""
                    **Vessel Information:**
                    - Name: {result['vessel_name']}
                    - MMSI: {result['mmsi']}
                    - Last Update: {result['last_timestamp']}
                    """)
                
                with metadata_col2:
                    model_mode = result.get("model_mode", "UNKNOWN")
                    model_label = "🤖 XGBoost (Real)" if model_mode == "REAL" else "📊 Demo (Simulated)"
                    st.info(f"""
                    **Prediction Parameters:**
                    - Historical Points: {seq_len}
                    - Model: {model_label}
                    - Prediction Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    """)
            
            else:
                st.error(f"❌ Prediction failed: {result.get('error', 'Unknown error')}")
        
        except Exception as e:
            st.error(f"❌ Error: {e}")

else:
    st.info("👈 Select a vessel from the sidebar to see predictions")

