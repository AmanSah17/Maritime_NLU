import streamlit as st
import requests
import re
import folium
from streamlit_folium import st_folium

st.title("⚓ Maritime Vessel Monitoring Chatbot")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_input = st.text_input("Ask about a vessel:")

if st.button("Send") and user_input:
    r = requests.post("http://127.0.0.1:8000/query", json={"text": user_input})
    response = r.json().get("response", "No response.")

    st.session_state.chat_history.append(("User", user_input))
    st.session_state.chat_history.append(("Bot", response))

for sender, msg in st.session_state.chat_history:
    if sender == "User":
        st.markdown(f"**You:** {msg}")
    else:
        st.markdown(f"**Bot:** {msg}")

    # Auto detect lat/lon for Folium map
    lat_lon = re.findall(r"(\d+\.\d+)°N, (\d+\.\d+)°E", msg)
    if lat_lon:
        lat, lon = map(float, lat_lon[0])
        m = folium.Map(location=[lat, lon], zoom_start=6)
        folium.Marker([lat, lon], tooltip=msg).add_to(m)
        st_folium(m, width=700, height=500)
