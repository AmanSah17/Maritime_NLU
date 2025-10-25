# XGBoost Integration Architecture

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     MARITIME DEFENSE DASHBOARD                  │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Streamlit)                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  pages/predictions.py - Predictions UI                 │   │
│  │  ├─ Vessel Selection (Dropdown)                        │   │
│  │  ├─ Sequence Length Slider (6-24)                      │   │
│  │  ├─ Prediction Metrics Display                         │   │
│  │  ├─ Interactive Folium Map                             │   │
│  │  │  ├─ Current Position (Green)                        │   │
│  │  │  ├─ Predicted Position (Cyan)                       │   │
│  │  │  ├─ Trajectory Line (Orange)                        │   │
│  │  │  └─ Historical Track (Cyan)                         │   │
│  │  └─ Model Mode Indicator (REAL/DEMO)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  HTTP Requests (JSON)                                           │
│  ↓                                                               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
                    http://127.0.0.1:8000
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI)                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  main.py - API Endpoints                               │   │
│  │  ├─ POST /predict/trajectory                           │   │
│  │  ├─ GET /predict/vessel/{name}                         │   │
│  │  └─ GET /predict/mmsi/{mmsi}                           │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  xgboost_predictor.py - ML Pipeline                    │   │
│  │  ├─ Singleton Pattern (Load Once)                      │   │
│  │  ├─ Feature Extraction (483 features)                  │   │
│  │  ├─ Haversine Features (7 features)                    │   │
│  │  ├─ StandardScaler Normalization                       │   │
│  │  ├─ PCA Transformation                                 │   │
│  │  ├─ XGBoost Prediction                                 │   │
│  │  └─ Demo Mode (Linear Extrapolation)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  db_handler.py - Database Access                       │   │
│  │  ├─ Fetch Vessel by Name                               │   │
│  │  ├─ Fetch Vessel by MMSI                               │   │
│  │  └─ Fetch Historical Track                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              ↓                                   │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│                    DATABASE (SQLite)                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  maritime_sample_0104.db                                        │
│  ├─ Vessels Table (10,063 vessels)                             │
│  │  ├─ MMSI, VesselName, CallSign                             │
│  │  ├─ LAT, LON, SOG, COG                                      │
│  │  ├─ BaseDateTime, Heading                                   │
│  │  └─ ... (28 total features)                                 │
│  └─ Indexed by MMSI and VesselName                             │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow Sequence

```
1. USER INTERACTION
   ├─ Select vessel from dropdown
   ├─ Adjust sequence_length slider
   └─ Click "🔮 Predict Trajectory"

2. FRONTEND REQUEST
   ├─ POST /predict/trajectory
   ├─ JSON: {"vessel": "NAME", "sequence_length": 12}
   └─ Show loading spinner

3. BACKEND PROCESSING
   ├─ Receive request
   ├─ Fetch vessel data from database
   │  └─ Query: SELECT * FROM vessels WHERE name=? LIMIT 22
   ├─ Pass to XGBoost predictor
   └─ Return predictions + map data

4. XGBOOST PREDICTION
   ├─ Extract last 12 historical points
   ├─ Extract 483 advanced features
   │  ├─ Statistical (mean, std, min, max, etc.)
   │  ├─ Trend (differences, volatility)
   │  └─ Autocorrelation (first-last ratios)
   ├─ Add 7 Haversine distance features
   ├─ Scale features (StandardScaler)
   ├─ Apply PCA transformation
   ├─ Generate predictions (REAL or DEMO)
   └─ Return [LAT, LON, SOG, COG]

5. RESPONSE GENERATION
   ├─ Combine predictions with metadata
   ├─ Generate map data
   │  ├─ Current position
   │  ├─ Predicted position
   │  └─ Historical track
   └─ Return JSON response

6. FRONTEND DISPLAY
   ├─ Parse response
   ├─ Display metrics (LAT, LON, SOG, COG)
   ├─ Render interactive map
   │  ├─ Current position marker (green)
   │  ├─ Predicted position marker (cyan)
   │  ├─ Trajectory line (orange)
   │  └─ Historical track (cyan)
   ├─ Show model mode (REAL/DEMO)
   └─ Display metadata
```

## Component Details

### 1. Frontend Component: predictions.py
**Location**: `backend/nlu_chatbot/frontend/pages/predictions.py`

**Responsibilities**:
- User interface for vessel selection
- Parameter adjustment (sequence length)
- API request handling
- Response parsing and display
- Map visualization
- Metrics presentation

**Key Functions**:
```python
# Fetch available vessels
fetch_vessels() → List[str]

# Send prediction request
requests.post("/predict/trajectory", json={...})

# Display map with predictions
st_folium(map_object)
```

### 2. Backend Endpoint: main.py
**Location**: `backend/nlu_chatbot/src/app/main.py`

**Endpoints**:
```python
@app.post("/predict/trajectory")
def predict_trajectory(request: PredictionRequest)

@app.get("/predict/vessel/{vessel_name}")
def predict_vessel_by_name(vessel_name: str)

@app.get("/predict/mmsi/{mmsi}")
def predict_vessel_by_mmsi(mmsi: int)
```

**Responsibilities**:
- Request validation
- Database queries
- Predictor invocation
- Response formatting

### 3. ML Pipeline: xgboost_predictor.py
**Location**: `backend/nlu_chatbot/src/app/xgboost_predictor.py`

**Key Classes**:
```python
class XGBoostPredictor:
    - Singleton pattern
    - Model loading
    - Feature extraction
    - Prediction generation
    - Demo mode fallback
```

**Methods**:
```python
extract_advanced_features(X) → 483 features
add_haversine_features(X) → 7 features
preprocess_and_predict(X) → predictions
predict_single_vessel(df) → Dict
_generate_demo_prediction(df) → predictions
```

### 4. Database: db_handler.py
**Location**: `backend/nlu_chatbot/src/app/db_handler.py`

**Key Methods**:
```python
fetch_vessel_by_name(name, end_dt) → DataFrame
fetch_vessel_by_mmsi(mmsi, end_dt) → DataFrame
fetch_track_ending_at(vessel_name, end_dt, limit) → DataFrame
```

## Feature Engineering Pipeline

### Stage 1: Advanced Feature Extraction (483 features)
For each dimension (LAT, LON, SOG, COG, Heading, etc.):

**Statistical Features** (10 per dimension):
- Mean, Std, Min, Max, Median
- P25, P75, Range, Skew, Kurtosis

**Trend Features** (4 per dimension):
- Mean of differences
- Std of differences
- Max of differences
- Min of differences

**Autocorrelation Features** (2 per dimension):
- First-last difference
- First-last ratio

**Volatility** (1 per dimension):
- Std of differences

**Total**: 17 features × 28 dimensions = 476 features

### Stage 2: Haversine Features (7 features)
- Mean distance to first point
- Max distance to first point
- Std distance to first point
- Total distance traveled
- Mean consecutive distance
- Max consecutive distance
- Std consecutive distances

### Stage 3: Preprocessing
1. **Scaling**: StandardScaler normalization
2. **Dimensionality Reduction**: PCA transformation
3. **Model Input**: Reduced feature space

## Model Modes

### REAL Mode
- Uses trained XGBoost model
- Requires model files in `results/xgboost_advanced_50_vessels/`
- High accuracy predictions
- ~100-200ms prediction time

### DEMO Mode
- Uses linear extrapolation
- No model files required
- Realistic predictions for testing
- ~10-50ms prediction time
- Clearly labeled in UI

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Model Load Time | ~2-5 seconds |
| Memory Usage | ~500MB |
| Prediction Time | 100-200ms (REAL), 10-50ms (DEMO) |
| Database Query | 50-100ms |
| Total Response | 200-400ms |
| Concurrent Requests | 4 workers |

## Security Considerations

1. **Model Protection**: Weights stay on backend
2. **Data Privacy**: Only predictions sent to frontend
3. **Input Validation**: All inputs validated
4. **Error Handling**: Graceful error responses
5. **Logging**: Comprehensive audit trail

## Scalability

- **Horizontal**: Multiple backend instances
- **Vertical**: Increase worker processes
- **Caching**: Vessel list cached (5 min TTL)
- **Batch Processing**: Support for multiple vessels
- **Async**: Non-blocking prediction requests

## Future Enhancements

1. **Confidence Intervals**: Uncertainty quantification
2. **Batch Predictions**: Multiple vessels at once
3. **Historical Accuracy**: Track prediction vs actual
4. **Model Retraining**: Periodic model updates
5. **Export Formats**: GeoJSON, KML, CSV
6. **Real-time Updates**: WebSocket predictions
7. **Anomaly Detection**: Identify unusual trajectories
8. **Route Optimization**: Suggest optimal paths

