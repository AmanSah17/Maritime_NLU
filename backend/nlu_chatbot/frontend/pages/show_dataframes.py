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

# Try to restore from cookies first (on page load/refresh)
if not st.session_state.get("authenticated"):
    AuthManager.restore_from_cookies()

# Check if user is authenticated
if not st.session_state.get("authenticated"):
    st.error("Please login first to access the dashboard")
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

st.markdown('<div class="defense-header"><h1> MARITIME VESSEL - Real time Trajectory Monitoring DASHBOARD</h1></div>', unsafe_allow_html=True)
#st.write("Advanced vessel tracking and time-series analysis for maritime operations")

backend_base = "http://127.0.0.1:8000"   #Our Backed Base url -- uvicorn 

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
    #st.markdown(f"**📧 Email:** `{st.session_state.username}`")
    st.markdown(f"** Role:** `{user_data.get('role', 'user')}`")

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
    st.markdown("### Quick search -- VESSELs")

    # Vessel search
    prefix = st.text_input("Search vessels", key="vessel_search")

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
st.header("Natural Language Engine for Vessel Tracking & Map Visualization")

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
    """Create latitude/longitude time series line plot"""
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

def create_latlon_bar_plot(track_data, vessel_name):
    """Create latitude/longitude historical bar plot with different colors"""
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

    # Create figure with secondary y-axis
    fig = go.Figure()

    # Add latitude bars
    fig.add_trace(go.Bar(
        x=timestamps, y=lats,
        name='Latitude',
        marker=dict(color='#00D9FF'),
        opacity=0.7,
        yaxis='y1'
    ))

    # Add longitude bars
    fig.add_trace(go.Bar(
        x=timestamps, y=lons,
        name='Longitude',
        marker=dict(color='#FF4444'),
        opacity=0.7,
        yaxis='y2'
    ))

    fig.update_layout(
        title=f'{vessel_name} - Latitude & Longitude Historical Bar Plot',
        xaxis_title='Time',
        yaxis=dict(
            title='Latitude (°)',
            title_font=dict(color='#00D9FF'),
            tickfont=dict(color='#00D9FF')
        ),
        yaxis2=dict(
            title='Longitude (°)',
            title_font=dict(color='#FF4444'),
            tickfont=dict(color='#FF4444'),
            overlaying='y',
            side='right'
        ),
        hovermode='x unified',
        template='plotly_dark',
        plot_bgcolor='rgba(0, 31, 63, 0.5)',
        paper_bgcolor='rgba(44, 62, 80, 0.8)',
        font=dict(color='#00D9FF', family='Courier New'),
        height=400,
        barmode='group'
    )

    return fig

# Initialize chat history in session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'query_responses' not in st.session_state:
    st.session_state.query_responses = {}

# Add custom CSS for chat interface
st.markdown("""
<style>
.chat-container {
    background: rgba(0, 31, 63, 0.3);
    border: 1px solid #00D9FF;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
    max-height: 600px;
    overflow-y: auto;
}

.chat-message-user {
    background: rgba(0, 217, 255, 0.1);
    border-left: 4px solid #00D9FF;
    padding: 12px;
    margin: 8px 0;
    border-radius: 4px;
    text-align: right;
}

.chat-message-bot {
    background: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4CAF50;
    padding: 12px;
    margin: 8px 0;
    border-radius: 4px;
    text-align: left;
}

.json-container {
    background: rgba(0, 31, 63, 0.5);
    border: 1px solid #FF9900;
    border-radius: 8px;
    padding: 15px;
    max-height: 600px;
    overflow-y: auto;
}

.entity-tag {
    display: inline-block;
    background: #00D9FF;
    color: #001F3F;
    padding: 4px 8px;
    border-radius: 4px;
    margin: 2px;
    font-weight: bold;
    font-size: 0.85em;
}
</style>
""", unsafe_allow_html=True)

# Main query interface with two columns
st.markdown('<div class="defense-header"><h2>🔍 Vessel Query & NLP Engine</h2></div>', unsafe_allow_html=True)

col_chat, col_json = st.columns([1.5, 1])

with col_chat:
    st.subheader("💬 Chat Interface")

    # Display chat history
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)

        if st.session_state.chat_history:
            for msg in st.session_state.chat_history:
                # Handle both dict and tuple formats
                if isinstance(msg, dict):
                    role = msg.get('role', 'bot')
                    content = msg.get('content', '')
                elif isinstance(msg, (tuple, list)) and len(msg) >= 2:
                    role = msg[0]
                    content = msg[1]
                else:
                    continue

                if role == 'user':
                    st.markdown(f'<div class="chat-message-user"><strong>You:</strong> {content}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message-bot"><strong>🤖 Engine:</strong> {content}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="chat-message-bot"><strong>🤖 Engine:</strong> Hello! I\'m your Maritime Defense AI Assistant. Ask me about vessel positions, tracks, or maritime data. Try: "Show last position of US GOV VESSEL"</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # Input area
    st.markdown("---")
    vessel_query = st.text_input("Enter your query:", value="", placeholder="e.g., Show last position of US GOV VESSEL")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit_btn = st.button("🔍 Query", use_container_width=True)
    with col_btn2:
        clear_btn = st.button("🗑️ Clear Chat", use_container_width=True)

    if clear_btn:
        st.session_state.chat_history = []
        st.session_state.query_responses = {}
        st.rerun()

    if submit_btn and vessel_query:
        try:
            with st.spinner("🔄 Processing query..."):
                r = requests.post(f"{backend_base}/query", json={"text": vessel_query}, timeout=35)
                payload = r.json()

                parsed = payload.get("parsed", {})
                response = payload.get("response", {})
                formatted = payload.get("formatted_response", "")

                # Add to chat history
                st.session_state.chat_history.append({"role": "user", "content": vessel_query})

                # Create a unique key for this query-response pair
                query_key = f"query_{len(st.session_state.chat_history)}"

                # Create elaborate, human-friendly response
                if 'LAT' in response and 'LON' in response:
                    vessel_name = response.get('VesselName', 'Unknown Vessel')
                    lat = response.get('LAT')
                    lon = response.get('LON')
                    sog = response.get('SOG', 0)
                    cog = response.get('COG', 0)
                    ts = response.get('BaseDateTime', 'Unknown Time')
                    heading = response.get('Heading', 0)

                    # Create elaborate response
                    elaborate_response = f"""
**Vessel Information:**
- **Name:** {vessel_name}
- **Last Position:** {lat:.4f}°N, {lon:.4f}°E
- **Speed:** {sog:.1f} knots
- **Course:** {cog:.0f}°
- **Heading:** {heading:.0f}°
- **Last Update:** {ts}

**Status:** ✅ Active and tracked in our maritime defense system.
"""

                    st.session_state.chat_history.append({"role": "bot", "content": elaborate_response})

                    # Store response data with unique key
                    st.session_state.query_responses[query_key] = {
                        "parsed": parsed,
                        "response": response,
                        "formatted": formatted
                    }

                    # Also store in session state for easy access
                    st.session_state['last_query_key'] = query_key

                    # Store track data
                    if 'track' in response and isinstance(response['track'], list):
                        st.session_state['current_track'] = response['track']
                        st.session_state['current_vessel'] = vessel_name
                else:
                    error_response = "❌ No vessel data found. Please try a different query or vessel name."
                    st.session_state.chat_history.append({"role": "bot", "content": error_response})

                    # Store response data even for errors
                    st.session_state.query_responses[query_key] = {
                        "parsed": parsed,
                        "response": response,
                        "formatted": formatted
                    }
                    st.session_state['last_query_key'] = query_key

                st.rerun()

        except Exception as e:
            error_msg = f"⚠️ Error processing query: {str(e)}"
            st.session_state.chat_history.append({"role": "bot", "content": error_msg})
            st.rerun()

with col_json:
    st.subheader("📊 Parsed Data & Entities")

    # Display latest response data
    if st.session_state.chat_history and 'last_query_key' in st.session_state:
        query_key = st.session_state.get('last_query_key')

        if query_key and query_key in st.session_state.query_responses:
            data = st.session_state.query_responses[query_key]

            # Create tabs for different data views
            tab_parsed, tab_entities, tab_formatted = st.tabs(["📋 Parsed JSON", "🏷️ Entities JSON", "📝 Formatted"])

            with tab_parsed:
                st.markdown("**NLP Parsed Query JSON:**")
                st.markdown('<div class="json-container">', unsafe_allow_html=True)
                parsed_data = data.get("parsed", {})
                if parsed_data:
                    st.json(parsed_data)
                else:
                    st.info("No parsed data available")
                st.markdown('</div>', unsafe_allow_html=True)

            with tab_entities:
                st.markdown("**Extracted Entities JSON:**")
                st.markdown('<div class="json-container">', unsafe_allow_html=True)
                response_data = data.get("response", {})

                if response_data:
                    # Display the full JSON data
                    st.json(response_data)
                else:
                    st.info("No entities extracted")

                st.markdown('</div>', unsafe_allow_html=True)

            with tab_formatted:
                st.markdown("**Formatted Response:**")
                st.markdown('<div class="json-container">', unsafe_allow_html=True)
                formatted_data = data.get("formatted", "")
                if formatted_data:
                    st.info(formatted_data)
                else:
                    st.info("No formatted response available")
                st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("📌 Query responses will appear here")
    else:
        st.info("📌 Submit a query to see extracted data and entities")
    

# Visualization section
st.markdown("---")
st.markdown('<div class="defense-header"><h2> Historical Track DASHBOARD </h2></div>', unsafe_allow_html=True)

if 'current_track' in st.session_state and st.session_state['current_track']:
    track_data = st.session_state['current_track']
    vessel_name = st.session_state.get('current_vessel', 'Unknown')

    # Save track to session
    SessionManager.save_track_data(track_data)

    # Visualization tabs
    tab_map_stats, tab_timeseries, tab_data = st.tabs([
        "🗺️ Map & Statistics",
        "📈 Time Series",
        "📥 Raw Data"
    ])

    with tab_map_stats:
        st.subheader("Interactive Map & Track Statistics")

        # Map section
        st.markdown("**Interactive Folium Map with Movement Arrows**")
        col_map1, col_map2 = st.columns([3, 1])

        with col_map1:
            try:
                m = create_track_map(track_data, vessel_name)
                if m:
                    st_folium(m, width=1200, height=500)
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

        # Statistics section
        st.markdown("---")
        st.markdown("**Track Statistics & Analysis**")

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

    with tab_timeseries:
        st.subheader("Time Series Analysis")

        # Create tabs for different metrics
        ts_col1, ts_col2 = st.columns(2)

        with ts_col1:
            st.markdown("**Speed Over Ground (SOG)**")
            try:
                fig_sog = create_time_series_dashboard(track_data, vessel_name)
                if fig_sog:
                    st.plotly_chart(fig_sog, use_container_width=True, key="sog_chart")
            except Exception as e:
                st.error(f"Error creating SOG plot: {e}")

        with ts_col2:
            st.markdown("**Position Over Time (Line Plot)**")
            try:
                fig_pos = create_position_plot(track_data, vessel_name)
                if fig_pos:
                    st.plotly_chart(fig_pos, use_container_width=True, key="position_line_chart")
            except Exception as e:
                st.error(f"Error creating position plot: {e}")

        st.markdown("---")

        ts_col3, ts_col4 = st.columns(2)

        with ts_col3:
            st.markdown("**Course & Heading**")
            try:
                fig_course = create_course_heading_plot(track_data, vessel_name)
                if fig_course:
                    st.plotly_chart(fig_course, use_container_width=True, key="course_heading_chart")
            except Exception as e:
                st.error(f"Error creating course plot: {e}")

        with ts_col4:
            st.markdown("**Latitude & Longitude (Bar Plot)**")
            try:
                fig_latlon = create_latlon_bar_plot(track_data, vessel_name)
                if fig_latlon:
                    st.plotly_chart(fig_latlon, use_container_width=True, key="latlon_bar_chart")
            except Exception as e:
                st.error(f"Error creating lat/lon bar plot: {e}")

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
    st.info("Pleas enter a vessel name or your Query  to see visualizations and time series data")



