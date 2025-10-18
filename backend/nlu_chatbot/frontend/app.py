import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium
import json

st.title("⚓ Maritime Vessel Monitoring Chatbot")

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

# No vessel quick search or directory per user request

if st.button("Send") and user_input:
    try:
        r = requests.post("http://127.0.0.1:8000/query", json={"text": user_input}, timeout=8)
        response = r.json().get("response", "No response.")
    except Exception as e:
        response = {"message": f"Backend request failed: {e}"}

    # append to conversation
    st.session_state.chat_history.append(("User", user_input))
    st.session_state.chat_history.append(("Bot", response))
    # update last bot response for outside display
    st.session_state.last_bot_response = response

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
            m = folium.Map(location=center, zoom_start=10, tiles='OpenStreetMap')
            # add icon markers for each point
            for lat, lon, when in coords:
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
    st.markdown("### Conversation")
    # make the conversation area scrollable by using an expander
    with st.expander("Conversation (click to open)", expanded=True):
        for idx, (sender, msg) in enumerate(st.session_state.chat_history):
            if sender == "User":
                st.markdown(f"**You:** {msg}")
            else:
                # Render concise Bot messages. Do not dump raw dicts into chat history
                if isinstance(msg, dict):
                    if msg.get('message'):
                        st.markdown(f"**Bot:** {msg.get('message')}")
                    else:
                        vessel = msg.get('VesselName', 'unknown')
                        lat = msg.get('LAT')
                        lon = msg.get('LON')
                        ts = msg.get('BaseDateTime') or msg.get('timestamp')
                        summary = f"Vessel: {vessel}"
                        if lat is not None and lon is not None:
                            summary += f", Position: {lat}, {lon}"
                        if ts:
                            summary += f", Time: {ts}"
                        st.markdown(f"**Bot:** {summary}")

                        # store track payload under message index so we can plot later
                        if 'track' in msg and isinstance(msg['track'], list) and len(msg['track'])>0:
                            st.session_state.track_store[str(idx)] = msg['track']
                            if st.button(f"Plot track (last 10 min) — message {idx}", key=f"plot_{idx}"):
                                st.session_state.map_to_plot = {
                                    "type": "track",
                                    "vessel": vessel,
                                    "points": msg['track']
                                }
                        else:
                            # No track available; show small helper text
                            st.info("No track data available for this response")
                else:
                    # simple text response
                    st.markdown(f"**Bot:** {msg}")

