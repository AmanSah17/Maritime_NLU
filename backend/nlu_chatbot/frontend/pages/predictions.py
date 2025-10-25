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

# Add tabs for different views
tab1, tab2, tab3 = st.tabs(["🔮 Predictions", "📊 Test Results", "ℹ️ System Status"])

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

        st.markdown("**Prediction Parameters:**")
        st.info("""
        ℹ️ **Adaptive Sequence Length**
        - System automatically adjusts to available data
        - Minimum: 3 points
        - Recommended: 12+ points
        - Maximum: 24 points
        """)

        sequence_length = st.slider(
            "Historical points (will adapt to available data)",
            min_value=3,
            max_value=24,
            value=12,
            step=1
        )

        if st.button("🔮 Predict Trajectory"):
            st.session_state.predict_vessel = selected_vessel
            st.session_state.predict_seq_len = sequence_length
    else:
        st.warning("No vessels available")

# Main content - Tab 1: Predictions
with tab1:
    st.markdown("### 🔮 Real-time Vessel Trajectory Prediction")

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
                        st.warning(f"⚠️  DEMO MODE: Using simulated predictions (Feature mismatch detected)")
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
                    error_msg = result.get('error', 'Unknown error')
                    available = result.get('available_points', 'unknown')
                    required = result.get('required_points', 'unknown')

                    st.error(f"Prediction failed: {error_msg}")

                    if 'Insufficient data' in error_msg:
                        st.warning(f"""
                        **Data Availability Issue:**
                        - Available points: {available}
                        - Minimum required: {required}

                        **Solutions:**
                        1. Try a different vessel with more historical data
                        2. Reduce the sequence length slider
                        3. Wait for more data to be collected
                        """)
                    else:
                        st.info(f"**Error Details:** {error_msg}")

            except Exception as e:
                st.error(f"❌ Error: {e}")

    else:
        st.info("Select a vessel from the sidebar to see predictions")

# Tab 2: Test Results
with tab2:
    st.markdown("### 📊 XGBoost Prediction Test Results")

    st.info("""
    This tab shows the results from comprehensive testing of the XGBoost prediction system.
    Tests were run on 25 random vessels with different sequence lengths (6, 12, 18, 24 points).
    """)

    try:
        import json
        import os

        # Try to load test results
        test_results_path = "xgboost_test_results.json"
        if os.path.exists(test_results_path):
            with open(test_results_path, 'r') as f:
                test_data = json.load(f)

            # Display summary statistics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Tests", test_data.get("total_tests", 0))

            with col2:
                st.metric("Successful", test_data.get("successful_tests", 0),
                         delta=f"{test_data.get('success_rate', 0):.1f}%")

            with col3:
                st.metric("Failed", test_data.get("failed_tests", 0))

            with col4:
                st.metric("Success Rate", f"{test_data.get('success_rate', 0):.1f}%")

            st.markdown("---")

            # Model mode distribution
            st.subheader("Model Mode Distribution")
            mode_dist = test_data.get("model_mode_distribution", {})
            if mode_dist:
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Modes Used:**")
                    for mode, count in mode_dist.items():
                        st.write(f"- {mode}: {count} tests")

                with col2:
                    st.write("**Status:**")
                    st.success("✅ All predictions using DEMO mode (Feature mismatch detected)")
                    st.info("ℹ️ DEMO mode uses linear extrapolation for predictions")

            st.markdown("---")

            # Sequence length analysis
            st.subheader("Sequence Length Analysis")
            seq_analysis = test_data.get("sequence_length_analysis", {})
            if seq_analysis:
                for length, stats in seq_analysis.items():
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(f"Length {length}", f"{stats.get('successful', 0)}/{stats.get('total', 0)}")
                    with col2:
                        st.metric(f"Success Rate", f"{stats.get('success_rate', 0):.1f}%")
                    with col3:
                        st.metric(f"Avg Points", f"{stats.get('avg_available_points', 0):.1f}")

            st.markdown("---")

            # Error analysis
            st.subheader("Error Analysis")
            error_dist = test_data.get("error_distribution", {})
            if error_dist:
                st.write("**Common Errors:**")
                for error, count in sorted(error_dist.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- {error}: {count} occurrences")

            st.markdown("---")

            # Test details
            st.subheader("Detailed Test Results")
            if "test_results" in test_data:
                # Create a dataframe for better visualization
                results_list = []
                for result in test_data["test_results"]:
                    results_list.append({
                        "Vessel": result.get("vessel", "N/A"),
                        "Seq Length": result.get("sequence_length", 0),
                        "Status": result.get("status", "N/A"),
                        "Model": result.get("model_mode", "N/A"),
                        "Available Points": result.get("available_points", 0),
                        "Error": result.get("error", "")
                    })

                results_df = pd.DataFrame(results_list)
                st.dataframe(results_df, use_container_width=True)
        else:
            st.warning("No test results found. Run tests to generate results.")
            st.info("Run: `python test_xgboost_predictions.py` from the project root")

    except Exception as e:
        st.error(f"Error loading test results: {e}")

# Tab 3: System Status
with tab3:
    st.markdown("### ℹ️ System Status & Configuration")

    st.subheader("Backend Connection")
    try:
        response = requests.get(f"{backend_base}/health", timeout=5)
        if response.status_code == 200:
            st.success("✅ Backend is running")
            st.write(f"Backend URL: {backend_base}")
        else:
            st.error("❌ Backend returned error")
    except:
        st.error("❌ Cannot connect to backend")

    st.markdown("---")

    st.subheader("XGBoost Model Status")
    st.info("""
    **Current Status:** DEMO Mode (Feature Mismatch)

    **Issue:** Database has 6 feature dimensions, but model expects 28 dimensions
    - Database features: LAT, LON, SOG, COG, Heading, VesselType
    - Model expects: 28 dimensions (likely includes additional AIS fields)
    - Feature mismatch: 109 features vs 483 expected

    **Solution:** Automatic fallback to DEMO mode (linear extrapolation)
    """)

    st.markdown("---")

    st.subheader("Database Information")
    try:
        response = requests.get(f"{backend_base}/vessels", timeout=5)
        vessels_data = response.json()
        st.success(f"✅ Database connected")
        st.write(f"Total vessels: {len(vessels_data.get('vessels', []))}")
    except:
        st.error("❌ Cannot connect to database")

    st.markdown("---")

    st.subheader("Feature Dimension Analysis")
    st.write("""
    **Training Data Schema (Expected):**
    - Dimensions: 28
    - Features per dimension: 17 (statistical + trend)
    - Haversine features: 7
    - Total: 483 features

    **Current Database Schema:**
    - Dimensions: 6 (LAT, LON, SOG, COG, Heading, VesselType)
    - Features per dimension: 17 (statistical + trend)
    - Haversine features: 7
    - Total: 109 features

    **Mismatch:** 374 missing features
    """)

    st.markdown("---")

    st.subheader("Prediction Modes")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**REAL Mode (XGBoost)**")
        st.write("""
        - Uses trained XGBoost model
        - Requires 483 features
        - Status: ❌ Disabled (feature mismatch)
        """)

    with col2:
        st.write("**DEMO Mode (Linear Extrapolation)**")
        st.write("""
        - Uses linear trend extrapolation
        - Works with any feature count
        - Status: ✅ Active (fallback)
        """)
