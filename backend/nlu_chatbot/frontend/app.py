import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium
import json
from datetime import datetime, timedelta
try:
    from dateutil import parser as _dateutil_parser
except Exception:
    _dateutil_parser = None

st.title("⚓ Maritime Vessel Monitoring Chatbot")

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
</style>
""", unsafe_allow_html=True)

# session state initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# store per-message track payloads so Plot buttons can render maps later
if "track_store" not in st.session_state:
    st.session_state.track_store = {}

# store last bot response separately so it can be shown outside the chat box
if "last_bot_response" not in st.session_state:
    st.session_state.last_bot_response = None

# store which map payload to render (either 'point' or 'track')
if "map_to_plot" not in st.session_state:
    st.session_state.map_to_plot = None

user_input = st.text_input("Ask about a vessel:")

# small timeline slider to control how many minutes of track to show when plotting
minutes_window = st.slider("Time window for track plotting (minutes)", min_value=1, max_value=120, value=10, step=1)

# No vessel quick search or directory per user request

# Helper to send a query and update session state (used by main input and sidebar selections)
def send_query(text: str):
    try:
        r = requests.post("http://127.0.0.1:8000/query", json={"text": text}, timeout=20)
        parsed = r.json().get("parsed", {})
        resp = r.json().get("response", "No response.")
        formatted_response = r.json().get("formatted_response", "")

        # Store formatted response for display
        if formatted_response:
            resp['_formatted_text'] = formatted_response

        # log the search on server
        try:
            requests.post("http://127.0.0.1:8000/admin/log_search", params={"query": text}, timeout=3)
        except Exception:
            pass
    except Exception as e:
        parsed = {}
        resp = {"message": f"Backend request failed: {e}"}

    st.session_state.chat_history.append(("User", text))
    st.session_state.chat_history.append(("Bot", resp))
    st.session_state.last_bot_response = resp

# Main send button behaviour
if st.button("Send") and user_input:
    send_query(user_input)

# Sidebar: Vessel directory (searchable)
with st.sidebar:
    st.markdown("### Vessel directory")
    # provide a typed-prefix search to avoid fetching all names
    prefix = st.text_input("Search vessels (type a few characters)", key="vessel_search")

    @st.cache_data(ttl=60)
    def fetch_vessel_prefix(q: str, limit: int = 20):
        try:
            r = requests.get("http://127.0.0.1:8000/vessels/search", params={"q": q, "limit": limit}, timeout=6)
            return r.json().get("vessels", [])
        except Exception:
            return []

    if prefix and len(prefix.strip()) >= 2:
        candidates = fetch_vessel_prefix(prefix.strip(), limit=20)
        if candidates:
            sel = st.selectbox("Matching vessels", options=candidates, key="vessel_select")

            # Auto-fetch on selection (async-like behavior)
            if sel and sel != st.session_state.get('last_selected_vessel'):
                st.session_state['last_selected_vessel'] = sel
                with st.spinner(f"🔍 Fetching data for {sel}..."):
                    qtext = f"show last position of {sel}"
                    send_query(qtext)
                st.rerun()
        else:
            st.info("No matches found for that prefix")
    else:
        st.info("Type at least 2 characters above to search vessel names (server-side prefix search)")

# Top area: show last bot response (human readable) and an interactive map area
st.markdown("### Last response")
if st.session_state.last_bot_response is None:
    st.info("No bot responses yet. Ask about a vessel to begin.")
else:
    resp = st.session_state.last_bot_response
    # Render a human-friendly summary outside the chat history
    if isinstance(resp, dict):
        if resp.get("message"):
            st.error(resp.get("message"))
        else:
            # Show formatted response if available
            if resp.get('_formatted_text'):
                st.success(resp.get('_formatted_text'))
            else:
                # Fallback to manual formatting
                vessel = resp.get('VesselName', 'unknown')
                lat = resp.get('LAT')
                lon = resp.get('LON')
                ts = resp.get('BaseDateTime') or resp.get('timestamp')
                summary = f"Vessel: {vessel}"
                if lat is not None and lon is not None:
                    summary += f", Position: {lat}, {lon}"
                if ts:
                    summary += f", Time: {ts}"
                st.success(summary)

            # If there's a single point (show), allow plotting that point on the map
            if lat is not None and lon is not None:
                if st.button("Plot last response on map", key="plot_last"):
                    st.session_state.map_to_plot = {
                        "type": "point",
                        "vessel": vessel,
                        "points": [{"LAT": lat, "LON": lon, "BaseDateTime": ts}],
                    }

            # If there's a track array, keep it stored and allow plotting
            if 'track' in resp and isinstance(resp['track'], list) and len(resp['track'])>0:
                st.session_state.track_store["last"] = resp['track']
                if st.button("Plot track (last 10 min)", key="plot_last_track"):
                    st.session_state.map_to_plot = {
                        "type": "track",
                        "vessel": vessel,
                        "points": resp['track']
                    }

# Map rendering area (outside the chatbox)
st.markdown("### Map")
map_col = st.container()
with map_col:
    if st.session_state.map_to_plot is not None:
        payload = st.session_state.map_to_plot
        points = payload.get('points', [])
        # Build coords list with most recent first if available
        coords = []
        for p in points:
            try:
                coords.append((float(p['LAT']), float(p['LON']), p.get('BaseDateTime')))
            except Exception:
                continue

        if coords:
            # center on most recent point
            center = [coords[0][0], coords[0][1]]
            # filter coords by minutes_window (keep only points within the window relative to most recent)
            def _parse_dt(s):
                if s is None:
                    return None
                if _dateutil_parser is not None:
                    try:
                        return _dateutil_parser.parse(s)
                    except Exception:
                        pass
                # try common formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
                    try:
                        return datetime.strptime(s, fmt)
                    except Exception:
                        continue
                return None

            most_recent_dt = _parse_dt(coords[0][2])
            if most_recent_dt is not None:
                cutoff = most_recent_dt - timedelta(minutes=int(minutes_window))
                filtered = []
                for lat, lon, when in coords:
                    dt = _parse_dt(when)
                    if dt is None or dt >= cutoff:
                        filtered.append((lat, lon, when))
                coords_to_plot = filtered if filtered else coords
            else:
                coords_to_plot = coords

            m = folium.Map(location=center, zoom_start=10, tiles='OpenStreetMap')
            # add icon markers for each point
            for lat, lon, when in coords_to_plot:
                folium.Marker(location=[lat, lon], popup=str(when), icon=folium.Icon(color='blue', icon='ship', prefix='fa')).add_to(m)

            st_folium(m, width=800, height=500)
            # allow download of the points as JSON
            try:
                fname = f"{payload.get('vessel','vessel')}_track.json"
                st.download_button("Download track JSON", data=json.dumps(points), file_name=fname, mime='application/json')
            except Exception:
                pass
        else:
            st.info("No valid points to plot on the map")
    else:
        st.info("No map selected. Use 'Plot' buttons in the conversation or the last-response controls to show a map.")

with st.container():
    st.markdown("### 💬 Conversation History")

    # Add CSS for scrollable chat container
    st.markdown("""
    <style>
    .chat-container {
        height: 500px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        background-color: #f9f9f9;
        margin-bottom: 15px;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196F3;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    .bot-message {
        background-color: #f5f5f5;
        border-left: 4px solid #4CAF50;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Display chat history in a scrollable container
    if st.session_state.chat_history:
        chat_html = '<div class="chat-container">'

        for idx, (sender, msg) in enumerate(st.session_state.chat_history):
            if sender == "User":
                chat_html += f'<div class="user-message"><b>👤 You:</b> {msg}</div>'
            else:
                # Render concise Bot messages
                if isinstance(msg, dict):
                    if msg.get('message'):
                        chat_html += f'<div class="bot-message"><b>🤖 Bot:</b> {msg.get("message")}</div>'
                    else:
                        # Show formatted response if available
                        if msg.get('_formatted_text'):
                            chat_html += f'<div class="bot-message"><b>🤖 Bot:</b> {msg.get("_formatted_text")}</div>'
                        else:
                            # Fallback to manual formatting
                            vessel = msg.get('VesselName', 'unknown')
                            lat = msg.get('LAT')
                            lon = msg.get('LON')
                            ts = msg.get('BaseDateTime') or msg.get('timestamp')
                            summary = f"Vessel: {vessel}"
                            if lat is not None and lon is not None:
                                summary += f", Position: {lat}, {lon}"
                            if ts:
                                summary += f", Time: {ts}"
                            chat_html += f'<div class="bot-message"><b>🤖 Bot:</b> {summary}</div>'

                        # store track payload under message index so we can plot later
                        if 'track' in msg and isinstance(msg['track'], list) and len(msg['track'])>0:
                            st.session_state.track_store[str(idx)] = msg['track']
                else:
                    # simple text response
                    chat_html += f'<div class="bot-message"><b>🤖 Bot:</b> {msg}</div>'

        chat_html += '</div>'
        st.markdown(chat_html, unsafe_allow_html=True)

        # Plot buttons for tracks
        st.markdown("---")
        st.markdown("**Plot Options:**")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📍 Plot Last Response"):
                if st.session_state.last_bot_response and isinstance(st.session_state.last_bot_response, dict):
                    resp = st.session_state.last_bot_response
                    if 'track' in resp and isinstance(resp['track'], list) and len(resp['track'])>0:
                        st.session_state.map_to_plot = {
                            "type": "track",
                            "vessel": resp.get('VesselName', 'unknown'),
                            "points": resp['track']
                        }
                        st.rerun()

        with col2:
            if st.button("🔄 Clear History"):
                st.session_state.chat_history = []
                st.session_state.last_bot_response = None
                st.rerun()

        with col3:
            if st.button("📥 Export Chat"):
                chat_text = "\n".join([f"{sender}: {msg}" for sender, msg in st.session_state.chat_history])
                st.download_button(
                    label="Download Chat",
                    data=chat_text,
                    file_name="chat_history.txt",
                    mime="text/plain"
                )
    else:
        st.info("💬 No conversation yet. Start by searching for a vessel or asking a question!")

