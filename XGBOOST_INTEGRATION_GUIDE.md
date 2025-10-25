# XGBoost Integration Guide

## Overview
This guide explains how the XGBoost trajectory prediction model is integrated into the Maritime Defense Dashboard. The model weights and pipeline remain on the backend, with only predictions sent to the frontend.

## Architecture

### Backend Components

#### 1. **XGBoost Predictor Module** (`backend/nlu_chatbot/src/app/xgboost_predictor.py`)
- **Purpose**: Loads and manages the pre-trained XGBoost model
- **Key Features**:
  - Singleton pattern for efficient model caching (loaded once)
  - Preprocessing pipeline: feature extraction, scaling, PCA transformation
  - Haversine distance calculations for spatial features
  - Advanced time-series feature extraction (483 features per dimension)

**Key Methods**:
```python
# Get global predictor instance
predictor = get_predictor()

# Predict for a single vessel
result = predictor.predict_single_vessel(vessel_df, sequence_length=12)
```

#### 2. **FastAPI Endpoints** (`backend/nlu_chatbot/src/app/main.py`)

**POST /predict/trajectory**
- Accepts vessel name or MMSI
- Fetches historical data from database
- Returns predictions with map data

```json
{
  "prediction_available": true,
  "predicted_lat": 40.7128,
  "predicted_lon": -74.0060,
  "predicted_sog": 12.5,
  "predicted_cog": 180.0,
  "last_known_lat": 40.7100,
  "last_known_lon": -74.0050,
  "vessel_name": "VESSEL_NAME",
  "mmsi": 123456789,
  "map_data": {
    "current_position": {...},
    "predicted_position": {...},
    "track": [...]
  }
}
```

**GET /predict/vessel/{vessel_name}**
- Quick prediction by vessel name

**GET /predict/mmsi/{mmsi}**
- Quick prediction by MMSI

### Frontend Components

#### 1. **Predictions Page** (`backend/nlu_chatbot/frontend/pages/predictions.py`)
- Interactive vessel selection
- Real-time prediction display
- Map visualization with current and predicted positions
- Historical track overlay
- Prediction metadata and statistics

## Data Flow

```
User Query (Parsed)
    ↓
Backend: /predict/trajectory endpoint
    ↓
Database: Fetch vessel historical data
    ↓
XGBoost Predictor:
    - Extract 483 advanced features
    - Add 7 Haversine features
    - Scale features
    - Apply PCA transformation
    - Generate predictions
    ↓
Return predictions + map data
    ↓
Frontend: Display on interactive map
```

## Model Preprocessing Pipeline

### 1. Feature Extraction (483 features)
For each dimension (LAT, LON, SOG, COG, etc.):
- **Statistical**: mean, std, min, max, median, p25, p75, range, skew, kurtosis
- **Trend**: mean, std, max, min of differences
- **Autocorrelation**: first-last difference, first-last ratio
- **Volatility**: standard deviation of differences

### 2. Haversine Features (7 features)
- Mean distance to first point
- Max distance to first point
- Std distance to first point
- Total distance traveled
- Mean consecutive distance
- Max consecutive distance
- Std consecutive distances

### 3. Scaling & PCA
- StandardScaler normalization
- PCA transformation for dimensionality reduction

## Setup Instructions

### 1. Ensure Model Files Exist
```
results/xgboost_advanced_50_vessels/
├── xgboost_model.pkl
├── scaler.pkl
└── pca.pkl
```

### 2. Start Backend
```bash
cd backend/nlu_chatbot/src
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Start Frontend
```bash
cd backend/nlu_chatbot/frontend
streamlit run app.py
```

### 4. Access Predictions
- Navigate to "🎯 Predictions" page from sidebar
- Select a vessel
- Adjust historical points (6-24)
- Click "🔮 Predict Trajectory"

## API Usage Examples

### Python
```python
import requests

# Predict by vessel name
response = requests.post(
    "http://127.0.0.1:8000/predict/trajectory",
    json={
        "vessel": "VESSEL_NAME",
        "sequence_length": 12
    }
)
result = response.json()
print(f"Predicted position: {result['predicted_lat']}, {result['predicted_lon']}")
```

### cURL
```bash
curl -X POST http://127.0.0.1:8000/predict/trajectory \
  -H "Content-Type: application/json" \
  -d '{"vessel": "VESSEL_NAME", "sequence_length": 12}'
```

## Error Handling

### Model Not Loaded
```json
{
  "error": "XGBoost model not available",
  "prediction_available": false,
  "message": "Model files not found in results/xgboost_advanced_50_vessels/"
}
```

### Insufficient Data
```json
{
  "error": "Insufficient data. Need 12 points, got 5",
  "prediction_available": false
}
```

### Vessel Not Found
```json
{
  "error": "No vessel data found",
  "prediction_available": false
}
```

## Performance Considerations

- **Model Loading**: Singleton pattern ensures model loads only once
- **Prediction Time**: ~100-200ms per vessel
- **Memory**: ~500MB for model + preprocessing objects
- **Caching**: Vessel list cached for 5 minutes on frontend

## Troubleshooting

### Model Files Not Found
1. Check `results/xgboost_advanced_50_vessels/` directory exists
2. Verify all three pickle files present
3. Check file permissions

### Slow Predictions
1. Check database query performance
2. Monitor backend CPU/memory
3. Reduce sequence_length if needed

### Map Not Displaying
1. Verify folium installation: `pip install folium streamlit-folium`
2. Check coordinate validity (LAT: -90 to 90, LON: -180 to 180)
3. Ensure map_data is included in response

## Future Enhancements

- [ ] Batch predictions for multiple vessels
- [ ] Confidence intervals for predictions
- [ ] Historical prediction accuracy metrics
- [ ] Real-time prediction updates
- [ ] Export predictions to GeoJSON
- [ ] Prediction comparison with actual positions

