import streamlit as st
import requests
import pandas as pd
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from auth_manager import AuthManager, SessionManager
from user_db import user_db

# Try to import send_query from utils, but don't fail if it doesn't exist
try:
    from utils import send_query
except ImportError:
    def send_query(text):
        """Fallback send_query function"""
        pass

try:
    from dateutil import parser as _dateutil_parser
except Exception:
    _dateutil_parser = None

# Initialize authentication
AuthManager.init_session_state()

# Check if user is authenticated
if not st.session_state.get("authenticated"):
    st.error("❌ Please login first to access the dashboard")
    if st.button("Go to Login"):
        st.switch_page("pages/auth.py")
    st.stop()

st.set_page_config(page_title="Maritime Defense Dashboard", layout="wide")

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

.defense-header {
    background: linear-gradient(90deg, #001F3F 0%, #2C3E50 50%, #001F3F 100%);
    border: 2px solid #00D9FF;
    border-radius: 4px;
    padding: 20px;
    margin: 20px 0;
    box-shadow: 0 0 20px rgba(0, 217, 255, 0.3);
    text-align: center;
}

.vessel-card {
    background: rgba(44, 62, 80, 0.7);
    border: 2px solid #00D9FF;
    border-radius: 4px;
    padding: 15px;
    margin: 10px 0;
    box-shadow: 0 0 10px rgba(0, 217, 255, 0.2);
}

.status-active {
    color: #00CC44;
    text-shadow: 0 0 10px rgba(0, 204, 68, 0.5);
}

.status-warning {
    color: #FF9900;
    text-shadow: 0 0 10px rgba(255, 153, 0, 0.5);
}

.status-alert {
    color: #FF4444;
    text-shadow: 0 0 10px rgba(255, 68, 68, 0.5);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="defense-header"><h1>⚓ MARITIME DEFENSE MONITORING DASHBOARD</h1></div>', unsafe_allow_html=True)
st.write("Advanced vessel tracking and time-series analysis for maritime operations")

backend_base = "http://127.0.0.1:8000"

# Session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "track_store" not in st.session_state:
    st.session_state.track_store = {}

if "last_bot_response" not in st.session_state:
    st.session_state.last_bot_response = None

if "map_to_plot" not in st.session_state:
    st.session_state.map_to_plot = None

# Sidebar: Authentication & Vessel Directory
with st.sidebar:
    st.markdown("### 🔐 AUTHENTICATION")

    # Display current user info
    user_data = st.session_state.get("user_data", {})
    st.markdown(f"**👤 User:** `{user_data.get('full_name', st.session_state.username)}`")
    st.markdown(f"**📧 Email:** `{st.session_state.username}`")
    st.markdown(f"**🎯 Role:** `{user_data.get('role', 'user')}`")

    # Verify token is still valid
    if st.session_state.auth_token:
        payload = AuthManager.verify_jwt_token(st.session_state.auth_token)
        if payload:
            st.markdown(f"**🟢 Status:** Active")
        else:
            st.warning("⚠️ Token expired, please login again")
            st.session_state.authenticated = False
            st.rerun()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Settings"):
            st.info("Settings coming soon")

    with col2:
        if st.button("🔓 Logout"):
            AuthManager.logout()
            st.success("✅ Logged out successfully")
            st.rerun()

    st.markdown("---")
    st.markdown("### 🚢 VESSEL DIRECTORY")

    # Vessel search
    prefix = st.text_input("Search vessels (2+ chars)", key="vessel_search")

    @st.cache_data(ttl=60)
    def fetch_vessel_prefix(q: str, limit: int = 20):
        try:
            r = requests.get(f"{backend_base}/vessels/search", params={"q": q, "limit": limit}, timeout=6)
            return r.json().get("vessels", [])
        except Exception:
            return []

    if prefix and len(prefix.strip()) >= 2:
        candidates = fetch_vessel_prefix(prefix.strip(), limit=20)
        if candidates:
            sel = st.selectbox("📍 Select vessel", options=candidates, key="vessel_select")
            if st.button("🎯 Quick Query Selected"):
                if st.session_state.get("authenticated"):
                    qtext = f"show last position of {sel}"
                    st.session_state['last_selected_vessel'] = sel
                    SessionManager.save_vessel_selection(sel, {"query": qtext})
                    send_query(qtext)
                    st.success(f"✅ Querying {sel}...")
                else:
                    st.error("❌ Please login first")
        else:
            st.info("No matches found")
    else:
        st.info("Type 2+ characters to search")



# ============================================================================
#  VESSEL TRACKING & MAP VISUALIZATION Code ---
# ============================================================================

st.markdown("---")
st.header("🗺️ Vessel Tracking & Map Visualization")

# Helper function to parse datetime
def parse_datetime(dt_str):
    """Parse datetime string to datetime object"""
    if dt_str is None:
        return None
    if isinstance(dt_str, datetime):
        return dt_str

    formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(str(dt_str), fmt)
        except:
            continue
    return None

# Helper function to create folium map with track
def create_track_map(track_data, vessel_name):
    """Create folium map with vessel track"""
    if not track_data or len(track_data) == 0:
        return None

    # Extract coordinates
    coords = []
    for point in track_data:
        try:
            lat = float(point.get('LAT'))
            lon = float(point.get('LON'))
            coords.append((lat, lon, point.get('BaseDateTime')))
        except:
            continue

    if not coords:
        return None

    # Center on most recent point
    center = [coords[0][0], coords[0][1]]

    # Create map
    m = folium.Map(location=center, zoom_start=12, tiles='OpenStreetMap')

    # Add polyline for track
    line_coords = [(lat, lon) for lat, lon, _ in coords]
    folium.PolyLine(
        line_coords,
        color='blue',
        weight=8,
        opacity=0.7,
        popup=f'{vessel_name} Track'
    ).add_to(m)

    # Add markers for each point
    for i, (lat, lon, ts) in enumerate(coords):
        if i == 0:
            # Most recent point - green
            color = 'green'
        elif i == len(coords) - 1:
            # Oldest point - red
            color = 'red'
        else:
            # Middle points - blue
            color = 'blue'

        popup_text = f"<b>{vessel_name}</b><br>Time: {ts}<br>Lat: {lat:.4f}, Lon: {lon:.4f}"

        folium.CircleMarker(
            location=(lat, lon),
            radius=12,
            popup=folium.Popup(popup_text, max_width=500),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=5
        ).add_to(m)

    return m

# Helper function to create time series dashboard
def create_time_series_dashboard(track_data, vessel_name):
    """Create interactive time series plots for vessel data"""
    if not track_data or len(track_data) == 0:
        return None

    # Extract data
    timestamps = []
    lats = []
    lons = []
    sogs = []
    cogs = []
    headings = []

    for point in track_data:
        try:
            timestamps.append(point.get('BaseDateTime'))
            lats.append(float(point.get('LAT', 0)))
            lons.append(float(point.get('LON', 0)))
            sogs.append(float(point.get('SOG', 0)))
            cogs.append(float(point.get('COG', 0)))
            headings.append(float(point.get('Heading', 0)))
        except:
            continue

    if not timestamps:
        return None

    # Create subplots
    fig = go.Figure()

    # Add traces for each metric
    fig.add_trace(go.Scatter(
        x=timestamps, y=sogs,
        mode='lines+markers',
        name='Speed (SOG)',
        line=dict(color='#00D9FF', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f'{vessel_name} - Speed Over Ground (SOG)',
        xaxis_title='Time',
        yaxis_title='Speed (knots)',
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(0, 31, 63, 0.5)',
        paper_bgcolor='rgba(44, 62, 80, 0.8)',
        font=dict(color='#00D9FF', family='Courier New'),
        height=400
    )

    return fig

def create_course_heading_plot(track_data, vessel_name):
    """Create course and heading visualization"""
    if not track_data or len(track_data) == 0:
        return None

    timestamps = []
    cogs = []
    headings = []

    for point in track_data:
        try:
            timestamps.append(point.get('BaseDateTime'))
            cogs.append(float(point.get('COG', 0)))
            headings.append(float(point.get('Heading', 0)))
        except:
            continue

    if not timestamps:
        return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps, y=cogs,
        mode='lines+markers',
        name='Course (COG)',
        line=dict(color='#00CC44', width=2),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=timestamps, y=headings,
        mode='lines+markers',
        name='Heading',
        line=dict(color='#FF9900', width=2, dash='dash'),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f'{vessel_name} - Course & Heading',
        xaxis_title='Time',
        yaxis_title='Degrees (°)',
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(0, 31, 63, 0.5)',
        paper_bgcolor='rgba(44, 62, 80, 0.8)',
        font=dict(color='#00D9FF', family='Courier New'),
        height=400
    )

    return fig

def create_position_plot(track_data, vessel_name):
    """Create latitude/longitude time series plot"""
    if not track_data or len(track_data) == 0:
        return None

    timestamps = []
    lats = []
    lons = []

    for point in track_data:
        try:
            timestamps.append(point.get('BaseDateTime'))
            lats.append(float(point.get('LAT', 0)))
            lons.append(float(point.get('LON', 0)))
        except:
            continue

    if not timestamps:
        return None

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=timestamps, y=lats,
        mode='lines+markers',
        name='Latitude',
        line=dict(color='#00D9FF', width=2),
        marker=dict(size=6)
    ))

    fig.add_trace(go.Scatter(
        x=timestamps, y=lons,
        mode='lines+markers',
        name='Longitude',
        line=dict(color='#FF4444', width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(
        title=f'{vessel_name} - Position Over Time',
        xaxis_title='Time',
        yaxis_title='Degrees',
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(0, 31, 63, 0.5)',
        paper_bgcolor='rgba(44, 62, 80, 0.8)',
        font=dict(color='#00D9FF', family='Courier New'),
        height=400
    )

    return fig

# Input section for vessel query
st.subheader("Query Vessel Position & Track")
vessel_query = st.text_input("Please enter your query:", value="Example: Show last position of US GOV VESSEL")

if st.button("🔍 Get Vessel Position & Track"):
    try:
        with st.spinner("Querying backend..."):
            r = requests.post(f"{backend_base}/query", json={"text": vessel_query}, timeout=15)
            payload = r.json()

            parsed = payload.get("parsed", {})
            response = payload.get("response", {})
            formatted = payload.get("formatted_response", "")

            # Create tabs for different response views
            tab1, tab2, tab3 = st.tabs(["📋 Bot Response", "📍 Last Position", "🏷️ Parsed Entities (NER)"])

            with tab1:
                st.subheader("Parsed Query")
                st.json(parsed)

            with tab2:
                st.subheader("Formatted Response")
                st.info(formatted)

            with tab3:
                st.subheader("Named Entity Recognition (NER)")
                st.json(response)

            # Check if we have position data
            if 'LAT' in response and 'LON' in response:
                vessel_name = response.get('VesselName', 'Unknown')
                lat = response.get('LAT')
                lon = response.get('LON')
                sog = response.get('SOG')
                cog = response.get('COG')
                ts = response.get('BaseDateTime')

                st.markdown("---")
                st.subheader(f"📍 Last Known Position: {vessel_name}")

                col_pos1, col_pos2 = st.columns(2)
                with col_pos1:
                    st.metric("Latitude", f"{lat:.4f}")
                    st.metric("Speed (knots)", f"{sog:.1f}" if sog else "N/A")
                with col_pos2:
                    st.metric("Longitude", f"{lon:.4f}")
                    st.metric("Course (°)", f"{cog:.0f}" if cog else "N/A")

                st.write(f"**Time:** {ts}")

                # Store track data in session state
                if 'track' in response and isinstance(response['track'], list):
                    st.session_state['current_track'] = response['track']
                    st.session_state['current_vessel'] = vessel_name
                    st.success(f"✅ Track data loaded: {len(response['track'])} positions")

            else:
                st.error("No position data found in response")
                st.json(response)

    except Exception as e:
        st.error(f"Request failed: {e}")
    

# Visualization section
st.markdown("---")
st.markdown('<div class="defense-header"><h2>� TIME SERIES DASHBOARD & VISUALIZATIONS</h2></div>', unsafe_allow_html=True)

if 'current_track' in st.session_state and st.session_state['current_track']:
    track_data = st.session_state['current_track']
    vessel_name = st.session_state.get('current_vessel', 'Unknown')

    # Save track to session
    SessionManager.save_track_data(track_data)

    # Visualization tabs
    tab_map, tab_timeseries, tab_stats, tab_data = st.tabs([
        "🗺️ Interactive Map",
        "📈 Time Series",
        "📊 Statistics",
        "� Raw Data"
    ])

    with tab_map:
        st.subheader("Interactive Folium Map with Movement Arrows")
        col_map1, col_map2 = st.columns([3, 1])

        with col_map1:
            try:
                m = create_track_map(track_data, vessel_name)
                if m:
                    st_folium(m, width=1200, height=600)
                else:
                    st.error("Could not create map from track data")
            except Exception as e:
                st.error(f"Error creating folium map: {e}")

        with col_map2:
            st.markdown("**Map Legend:**")
            st.markdown("🟢 **Green** - Most Recent")
            st.markdown("🔵 **Blue** - Middle Points")
            st.markdown("🔴 **Red** - Oldest")
            st.markdown("➡️ **Arrows** - Movement Pattern")

    with tab_timeseries:
        st.subheader("Time Series Analysis")

        # Create tabs for different metrics
        ts_col1, ts_col2 = st.columns(2)

        with ts_col1:
            st.markdown("**Speed Over Ground (SOG)**")
            try:
                fig_sog = create_time_series_dashboard(track_data, vessel_name)
                if fig_sog:
                    st.plotly_chart(fig_sog, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating SOG plot: {e}")

        with ts_col2:
            st.markdown("**Position Over Time**")
            try:
                fig_pos = create_position_plot(track_data, vessel_name)
                if fig_pos:
                    st.plotly_chart(fig_pos, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating position plot: {e}")

        st.markdown("---")

        ts_col3, ts_col4 = st.columns(2)

        with ts_col3:
            st.markdown("**Course & Heading**")
            try:
                fig_course = create_course_heading_plot(track_data, vessel_name)
                if fig_course:
                    st.plotly_chart(fig_course, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating course plot: {e}")

        with ts_col4:
            st.markdown("**Latitude & Longitude**")
            try:
                fig_latlon = create_position_plot(track_data, vessel_name)
                if fig_latlon:
                    st.plotly_chart(fig_latlon, use_container_width=True)
            except Exception as e:
                st.error(f"Error creating lat/lon plot: {e}")

    with tab_stats:
        st.subheader("Track Statistics & Analysis")

        # Calculate statistics
        stats_data = []
        for point in track_data:
            try:
                stats_data.append({
                    'timestamp': point.get('BaseDateTime'),
                    'lat': float(point.get('LAT', 0)),
                    'lon': float(point.get('LON', 0)),
                    'sog': float(point.get('SOG', 0)),
                    'cog': float(point.get('COG', 0)),
                    'heading': float(point.get('Heading', 0))
                })
            except:
                continue

        if stats_data:
            stats_df = pd.DataFrame(stats_data)

            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)

            with col_stat1:
                st.metric("📍 Total Points", len(stats_df))

            with col_stat2:
                avg_speed = stats_df['sog'].mean()
                st.metric("⚡ Avg Speed", f"{avg_speed:.2f} knots")

            with col_stat3:
                max_speed = stats_df['sog'].max()
                st.metric("🚀 Max Speed", f"{max_speed:.2f} knots")

            with col_stat4:
                min_speed = stats_df['sog'].min()
                st.metric("🐢 Min Speed", f"{min_speed:.2f} knots")

            st.markdown("---")

            # Additional statistics
            col_stat5, col_stat6, col_stat7 = st.columns(3)

            with col_stat5:
                avg_course = stats_df['cog'].mean()
                st.metric("🧭 Avg Course", f"{avg_course:.0f}°")

            with col_stat6:
                lat_range = stats_df['lat'].max() - stats_df['lat'].min()
                st.metric("📏 Lat Range", f"{lat_range:.4f}°")

            with col_stat7:
                lon_range = stats_df['lon'].max() - stats_df['lon'].min()
                st.metric("📏 Lon Range", f"{lon_range:.4f}°")

    with tab_data:
        st.subheader("Raw Track Data")
        track_df = pd.DataFrame(track_data)
        st.dataframe(track_df, use_container_width=True)

        # Export options
        col_export1, col_export2 = st.columns(2)

        with col_export1:
            csv = track_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"{vessel_name}_track.csv",
                mime="text/csv"
            )

        with col_export2:
            json_data = track_df.to_json(orient='records', indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"{vessel_name}_track.json",
                mime="application/json"
            )

else:
    st.info("🔍 Query a vessel first to see visualizations and time series data")

# SQL Index Creation (to be run in the database, not in Streamlit)
"""
CREATE INDEX IF NOT EXISTS idx_vessel_mmsi ON vessel_data(MMSI);
CREATE INDEX IF NOT EXISTS idx_vessel_basedatetime ON vessel_data(BaseDateTime);
"""
