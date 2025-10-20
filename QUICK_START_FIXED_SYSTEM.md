# Maritime NLU - Quick Start Guide (Fixed System)

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies
```bash
cd backend/nlu_chatbot
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Step 2: Start Backend Server
```bash
cd src/app
uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     ✅ Loaded 10063 vessels from maritime_sample_0104.db
```

### Step 3: Start Frontend (in new terminal)
```bash
cd frontend
streamlit run app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 4: Test the System
Open browser to `http://localhost:8501` and try:
- "show LAVACA"
- "show TREASURE COAST"
- "where is LAVACA"

---

## 🧪 Run Tests

### Test All Fixes
```bash
cd backend/nlu_chatbot
python test_all_fixes.py
```

**Expected Output:**
```
✅ TEST 1: Database Connection - PASS
✅ TEST 2: NLU Vessel Name Extraction - PASS
✅ TEST 3: Intent Executor - PASS
✅ TEST 4: Response Formatter - PASS
✅ TEST 5: Map Generation - PASS
✅ TEST 6: DateTime Parsing - PASS
```

### Run Unit Tests
```bash
$env:PYTHONPATH='src'
python -m pytest -v
```

---

## 📝 API Examples

### Query Endpoint
```bash
curl -X POST http://127.0.0.1:8000/query \
  -H "Content-Type: application/json" \
  -d '{"text": "show LAVACA"}'
```

**Response:**
```json
{
  "parsed": {
    "intent": "SHOW",
    "vessel_name": "LAVACA",
    "datetime": "2025-10-19 18:25:00"
  },
  "response": {
    "VesselName": "LAVACA",
    "LAT": 29.98157,
    "LON": -93.88125,
    "SOG": 1.3,
    "COG": 180.0,
    "track": [...]
  },
  "formatted_response": "LAVACA is currently at position 29.9816° N, 93.8813° W traveling at 1.3 knots heading South (180°)."
}
```

### Search Vessels
```bash
curl http://127.0.0.1:8000/vessels/search?q=LAV&limit=10
```

**Response:**
```json
{
  "vessels": ["LAVACA", "LAVACA II", "LAVACA III"]
}
```

### List All Vessels
```bash
curl http://127.0.0.1:8000/vessels
```

---

## 🗺️ Using Maps in Python

### Generate Folium Map
```python
from app.map_generator import MapGenerator
from app.db_handler import MaritimeDB
from app.intent_executor import IntentExecutor
from app.nlp_interpreter import MaritimeNLPInterpreter

# Setup
db = MaritimeDB('maritime_sample_0104.db')
nlp = MaritimeNLPInterpreter(vessel_list=db.get_all_vessel_names())
executor = IntentExecutor(db)

# Query
parsed = nlp.parse_query("show LAVACA")
response = executor.handle(parsed)

# Generate map
m = MapGenerator.create_vessel_track_map(
    response['track'],
    response['VesselName']
)
m.save('vessel_track.html')
```

### Generate GeoPandas GeoDataFrame
```python
gdf = MapGenerator.create_geopandas_track(
    response['track'],
    response['VesselName']
)

# Analyze
print(f"Track length: {len(gdf)} points")
print(f"Bounds: {gdf.total_bounds}")

# Export to GeoJSON
geojson = MapGenerator.geopandas_to_geojson(gdf)
```

### Create Prediction Map
```python
m = MapGenerator.create_prediction_map(
    current_position=(29.98157, -93.88125),
    predicted_position=(30.0, -93.9),
    vessel_name="LAVACA",
    duration_minutes=30
)
m.save('prediction.html')
```

---

## 💬 Using Response Formatter

```python
from app.response_formatter import ResponseFormatter

# Format SHOW response
formatted = ResponseFormatter.format_show_response(response)
print(formatted)
# Output: "LAVACA is currently at position 29.9816° N, 93.8813° W..."

# Format PREDICT response
formatted = ResponseFormatter.format_predict_response(response)
print(formatted)
# Output: "Based on current speed and course, LAVACA will be at..."

# Format VERIFY response
formatted = ResponseFormatter.format_verify_response(response)
print(formatted)
# Output: "✅ LAVACA's movement appears consistent and normal."
```

---

## ⚡ Using Async Database

```python
import asyncio
from app.db_handler_async import MaritimeDBAsync

async def main():
    db = MaritimeDBAsync('maritime_sample_0104.db')
    await db.connect()
    
    # Get all vessels
    vessels = await db.get_all_vessel_names()
    print(f"Found {len(vessels)} vessels")
    
    # Search by prefix
    results = await db.search_vessels_prefix("LAV", limit=10)
    print(f"Search results: {results}")
    
    # Fetch vessel track
    track = await db.fetch_track_ending_at("LAVACA", "2020-01-04 22:16:15", 60)
    print(f"Track has {len(track)} points")
    
    await db.close()

asyncio.run(main())
```

---

## 🐛 Troubleshooting

### Issue: "No vessels found"
**Solution:** Backend is using empty database
- Check logs: Should show "✅ Loaded 10063 vessels from maritime_sample_0104.db"
- Restart backend: `uvicorn main:app --reload`

### Issue: "Vessel name not extracted"
**Solution:** Try different query formats
- ✅ "show LAVACA"
- ✅ "show +BRAVA"
- ✅ "where is TREASURE COAST"
- ❌ "show vessel LAVACA" (too many words)

### Issue: "ModuleNotFoundError: No module named 'geopandas'"
**Solution:** Install missing dependencies
```bash
pip install geopandas shapely aiosqlite
```

### Issue: "spaCy model not found"
**Solution:** Download the model
```bash
python -m spacy download en_core_web_sm
```

---

## 📊 Database Info

### Sample Database
- **File:** `maritime_sample_0104.db`
- **Vessels:** 10,063 unique vessels
- **Records:** ~500,000 AIS positions
- **Date Range:** 2020-01-04
- **Size:** ~50 MB

### Main Database
- **File:** `maritime_data.db`
- **Status:** Empty (for user data)
- **Auto-fallback:** Yes (uses sample if empty)

---

## 🎯 Common Queries

```
# Show vessel position
"show LAVACA"
"where is TREASURE COAST"
"display +BRAVA"

# Predict trajectory
"predict where LAVACA will be in 30 minutes"
"where will TREASURE COAST be after 1 hour"

# Verify movement
"check if LAVACA's movement is consistent"
"verify TREASURE COAST"

# Search vessels
"find vessels starting with LAV"
"search for TREASURE"
```

---

## 📈 Performance Tips

1. **Use prefix search for large datasets**
   - `/vessels/search?q=LAV` (fast)
   - `/vessels` (slow for 10k+ vessels)

2. **Limit track queries**
   - Default: 60 minutes of history
   - Adjust: `duration_minutes` parameter

3. **Use async for concurrent requests**
   - `MaritimeDBAsync` for non-blocking queries
   - Better for web applications

4. **Cache results**
   - Vessel list (changes rarely)
   - Track data (time-based)

---

## 🔗 Useful Links

- **API Docs:** http://127.0.0.1:8000/docs
- **Frontend:** http://localhost:8501
- **Backend Health:** http://127.0.0.1:8000/health

---

## ✅ Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 8501
- [ ] Sample database loaded (10,063 vessels)
- [ ] Can query "show LAVACA"
- [ ] Formatted response displayed
- [ ] Map visualization working
- [ ] Tests passing

---

**Status:** ✅ System Ready for Use
**Last Updated:** 2025-10-19

