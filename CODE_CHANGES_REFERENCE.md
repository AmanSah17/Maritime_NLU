# Maritime NLU - Code Changes Reference

**Date:** 2025-10-19  
**Purpose:** Quick reference for all code changes made

---

## 📝 File 1: app.py (Main Chat Interface)

### Change 1: Enhanced send_query() function (Lines 38-61)

**Before:**
```python
def send_query(text: str):
    try:
        r = requests.post("http://127.0.0.1:8000/query", json={"text": text}, timeout=20)
        parsed = r.json().get("parsed", {})
        resp = r.json().get("response", "No response.")
    except Exception as e:
        parsed = {}
        resp = {"message": f"Backend request failed: {e}"}

    st.session_state.chat_history.append(("User", text))
    st.session_state.chat_history.append(("Bot", resp))
    st.session_state.last_bot_response = resp
```

**After:**
```python
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
```

**Key Changes:**
- ✅ Extract `formatted_response` from backend
- ✅ Store in `_formatted_text` field
- ✅ Use for display in UI

---

### Change 2: Updated response display (Lines 94-119)

**Before:**
```python
st.markdown("### Last response")
if st.session_state.last_bot_response is None:
    st.info("No bot responses yet. Ask about a vessel to begin.")
else:
    resp = st.session_state.last_bot_response
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
```

**After:**
```python
st.markdown("### Last response")
if st.session_state.last_bot_response is None:
    st.info("No bot responses yet. Ask about a vessel to begin.")
else:
    resp = st.session_state.last_bot_response
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
```

**Key Changes:**
- ✅ Check for `_formatted_text` first
- ✅ Display formatted response if available
- ✅ Fallback to manual formatting if not

---

### Change 3: Updated conversation display (Lines 204-247)

**Before:**
```python
for idx, (sender, msg) in enumerate(st.session_state.chat_history):
    if sender == "User":
        st.markdown(f"**You:** {msg}")
    else:
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
```

**After:**
```python
for idx, (sender, msg) in enumerate(st.session_state.chat_history):
    if sender == "User":
        st.markdown(f"**You:** {msg}")
    else:
        if isinstance(msg, dict):
            if msg.get('message'):
                st.markdown(f"**Bot:** {msg.get('message')}")
            else:
                # Show formatted response if available
                if msg.get('_formatted_text'):
                    st.markdown(f"**Bot:** {msg.get('_formatted_text')}")
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
                    st.markdown(f"**Bot:** {summary}")
```

**Key Changes:**
- ✅ Display formatted response in conversation
- ✅ Fallback to manual formatting
- ✅ Consistent with response display

---

## 📝 File 2: show_dataframes.py (Vessel Tracking Page)

### Change 1: Added imports (Lines 1-14)

**Added:**
```python
import folium
from streamlit_folium import st_folium
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
```

---

### Change 2: Added helper functions (Lines 100-200)

**Added:**
```python
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
        weight=2,
        opacity=0.7,
        popup=f'{vessel_name} Track'
    ).add_to(m)
    
    # Add markers for each point
    for i, (lat, lon, ts) in enumerate(coords):
        if i == 0:
            color = 'green'
            prefix = 'Start'
        elif i == len(coords) - 1:
            color = 'red'
            prefix = 'End'
        else:
            color = 'blue'
            prefix = f'Point {i}'
        
        popup_text = f"<b>{vessel_name}</b><br>Time: {ts}<br>Lat: {lat:.4f}, Lon: {lon:.4f}"
        
        folium.CircleMarker(
            location=(lat, lon),
            radius=6,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    return m

def create_geopandas_plot(track_data, vessel_name):
    """Create matplotlib plot with geopandas"""
    if not track_data or len(track_data) == 0:
        return None
    
    # Extract coordinates
    geometry = []
    data = []
    
    for i, point in enumerate(track_data):
        try:
            lat = float(point.get('LAT'))
            lon = float(point.get('LON'))
            geometry.append(Point(lon, lat))
            data.append({
                'vessel_name': vessel_name,
                'timestamp': point.get('BaseDateTime'),
                'lat': lat,
                'lon': lon,
                'sog': point.get('SOG'),
                'cog': point.get('COG'),
                'order': i
            })
        except:
            continue
    
    if not geometry:
        return None
    
    # Create GeoDataFrame
    gdf = gpd.GeoDataFrame(data, geometry=geometry, crs='EPSG:4326')
    
    # Create matplotlib figure
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Plot all points
    gdf.plot(ax=ax, alpha=0.5, edgecolor='k', color='lightblue', markersize=50)
    
    # Highlight last 10 points with different colors
    if len(gdf) > 10:
        last_10 = gdf.tail(10)
    else:
        last_10 = gdf
    
    # Plot last 10 with gradient colors
    colors = plt.cm.RdYlGn(range(len(last_10)))
    for idx, (i, row) in enumerate(last_10.iterrows()):
        ax.plot(row.geometry.x, row.geometry.y, 'o', color=colors[idx], markersize=12, zorder=5)
        ax.annotate(f"{idx}", (row.geometry.x, row.geometry.y), fontsize=8, ha='center')
    
    # Draw polyline connecting last 10 points
    if len(last_10) > 1:
        coords = [(row.geometry.x, row.geometry.y) for _, row in last_10.iterrows()]
        lons, lats = zip(*coords)
        ax.plot(lons, lats, 'r-', linewidth=2, alpha=0.7, label='Last 10 positions')
    
    # Mark the most recent position
    if len(gdf) > 0:
        most_recent = gdf.iloc[0]
        ax.plot(most_recent.geometry.x, most_recent.geometry.y, 'g*', markersize=30, 
                label='Most Recent', zorder=10)
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_title(f'{vessel_name} - Last 10 Positions Track')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    return fig
```

---

### Change 3: Added vessel tracking section (Lines 200-390)

**Added:**
```python
st.markdown("---")
st.header("🗺️ Vessel Tracking & Map Visualization")

# Input section for vessel query
st.subheader("Query Vessel Position & Track")
vessel_query = st.text_input("Enter vessel name or query:", value="show LAVACA")

col1, col2 = st.columns(2)

with col1:
    if st.button("Get Vessel Position & Track"):
        try:
            with st.spinner("Querying backend..."):
                r = requests.post(f"{backend_base}/query", json={"text": vessel_query}, timeout=15)
                payload = r.json()
                
                parsed = payload.get("parsed", {})
                response = payload.get("response", {})
                formatted = payload.get("formatted_response", "")
                
                st.subheader("Parsed Query")
                st.json(parsed)
                
                st.subheader("Formatted Response")
                st.info(formatted)
                
                # Check if we have position data
                if 'LAT' in response and 'LON' in response:
                    vessel_name = response.get('VesselName', 'Unknown')
                    lat = response.get('LAT')
                    lon = response.get('LON')
                    sog = response.get('SOG')
                    cog = response.get('COG')
                    ts = response.get('BaseDateTime')
                    
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
st.subheader("🗺️ Visualizations")

if 'current_track' in st.session_state and st.session_state['current_track']:
    track_data = st.session_state['current_track']
    vessel_name = st.session_state.get('current_vessel', 'Unknown')
    
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        if st.button("📍 Show Folium Map (Interactive)"):
            st.session_state['show_folium'] = True
    
    with viz_col2:
        if st.button("📊 Show GeoPandas Plot (Last 10)"):
            st.session_state['show_geopandas'] = True
    
    # Display Folium map
    if st.session_state.get('show_folium', False):
        st.subheader("Interactive Folium Map")
        try:
            m = create_track_map(track_data, vessel_name)
            if m:
                st_folium(m, width=1000, height=600)
            else:
                st.error("Could not create map from track data")
        except Exception as e:
            st.error(f"Error creating folium map: {e}")
    
    # Display GeoPandas plot
    if st.session_state.get('show_geopandas', False):
        st.subheader("GeoPandas Visualization (Last 10 Positions)")
        try:
            fig = create_geopandas_plot(track_data, vessel_name)
            if fig:
                st.pyplot(fig)
            else:
                st.error("Could not create geopandas plot from track data")
        except Exception as e:
            st.error(f"Error creating geopandas plot: {e}")
    
    # Show track data table
    if st.checkbox("Show track data table"):
        st.subheader("Track Data")
        track_df = pd.DataFrame(track_data)
        st.dataframe(track_df, use_container_width=True)
else:
    st.info("Query a vessel first to see visualizations")
```

---

## 📊 Summary of Changes

| File | Changes | Lines | Status |
|------|---------|-------|--------|
| app.py | 3 sections updated | 38-61, 94-119, 204-247 | ✅ Complete |
| show_dataframes.py | Imports + 3 functions + section | 1-14, 100-390 | ✅ Complete |

---

## 🎯 Key Improvements

✅ **Formatted Responses** - Human-friendly text display  
✅ **Folium Maps** - Interactive visualization with color-coded markers  
✅ **GeoPandas Plots** - Last 10 positions with movement patterns  
✅ **Session State** - Persistent data across interactions  
✅ **Error Handling** - Graceful fallbacks and error messages  
✅ **User Experience** - Intuitive UI with clear instructions  

---

**Last Updated:** 2025-10-19  
**Status:** ✅ All Changes Complete

