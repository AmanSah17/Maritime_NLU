# XGBoost Predictions - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Step 1: Start Backend
```bash
cd backend/nlu_chatbot/src
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
✅ You should see: `Uvicorn running on http://127.0.0.1:8000`

### Step 2: Start Frontend
```bash
cd backend/nlu_chatbot/frontend
streamlit run app.py
```
✅ You should see: `Local URL: http://localhost:8501`

### Step 3: Login
- Go to http://localhost:8501
- Login with:
  - Email: `amansah1717@gmail.com`
  - Password: `maritime_defense_2025`

### Step 4: Access Predictions
- Click "🎯 Predictions" in the sidebar
- Select a vessel from the dropdown
- Click "🔮 Predict Trajectory"
- View predictions on the map!

## 📊 What You'll See

### Prediction Metrics
- **Current Position**: Green marker on map
- **Predicted Position**: Cyan marker on map
- **Trajectory Line**: Orange line connecting current to predicted
- **Historical Track**: Cyan line showing past positions

### Data Displayed
- Current LAT/LON and Predicted LAT/LON
- Current SOG (Speed Over Ground) and Predicted SOG
- Current COG (Course Over Ground) and Predicted COG
- Vessel name, MMSI, and last update timestamp

### Model Mode
- **DEMO**: Using simulated predictions (model files not found)
- **REAL**: Using actual XGBoost model predictions

## 🔧 Configuration

### Adjust Prediction Parameters
- **Historical Points**: Slider from 6 to 24 points
  - Lower = faster, less accurate
  - Higher = slower, more accurate
  - Default = 12 points

### Change Vessel
- Select different vessel from dropdown
- Predictions update automatically

## 📍 API Endpoints

### Get Prediction by Vessel Name
```bash
curl -X POST http://127.0.0.1:8000/predict/trajectory \
  -H "Content-Type: application/json" \
  -d '{"vessel": "VESSEL_NAME", "sequence_length": 12}'
```

### Get Prediction by MMSI
```bash
curl -X POST http://127.0.0.1:8000/predict/trajectory \
  -H "Content-Type: application/json" \
  -d '{"mmsi": 123456789, "sequence_length": 12}'
```

### Quick Endpoints
```bash
# By vessel name
curl http://127.0.0.1:8000/predict/vessel/VESSEL_NAME

# By MMSI
curl http://127.0.0.1:8000/predict/mmsi/123456789
```

## 🎯 Use Cases

### 1. Real-time Vessel Tracking
- Monitor vessel movements
- Predict next positions
- Plan interception routes

### 2. Maritime Safety
- Identify anomalous trajectories
- Predict collision risks
- Alert on course changes

### 3. Port Operations
- Predict vessel arrival times
- Optimize dock assignments
- Plan resource allocation

### 4. Fleet Management
- Track multiple vessels
- Predict fleet movements
- Optimize routes

## ⚙️ Enable Real XGBoost Model

To use the actual trained XGBoost model instead of demo mode:

1. **Obtain Model Files**:
   - `xgboost_model.pkl`
   - `scaler.pkl`
   - `pca.pkl`

2. **Create Directory**:
   ```bash
   mkdir -p results/xgboost_advanced_50_vessels
   ```

3. **Place Files**:
   ```
   results/xgboost_advanced_50_vessels/
   ├── xgboost_model.pkl
   ├── scaler.pkl
   └── pca.pkl
   ```

4. **Restart Backend**:
   ```bash
   cd backend/nlu_chatbot/src
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

5. **Verify**: Model mode should show "🤖 XGBoost (Real)" instead of "📊 Demo (Simulated)"

## 🐛 Troubleshooting

### Backend Won't Start
```
ERROR: [WinError 10013] An attempt was made to access a socket...
```
**Solution**: Port 8000 is in use. Try:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

### No Vessels Available
**Solution**: Ensure database has data:
```bash
# Check database
python -c "from app.db_handler import MaritimeDB; db = MaritimeDB('maritime_sample_0104.db'); print(len(db.get_all_vessel_names()))"
```

### Predictions Not Showing
**Solution**: 
1. Check backend is running: `http://127.0.0.1:8000/vessels`
2. Check frontend console for errors
3. Verify vessel has sufficient historical data (need at least 12 points)

### Map Not Displaying
**Solution**: 
1. Ensure folium is installed: `pip install folium streamlit-folium`
2. Check coordinates are valid (LAT: -90 to 90, LON: -180 to 180)
3. Refresh page

## 📚 Documentation

- **Full Guide**: See `XGBOOST_INTEGRATION_GUIDE.md`
- **Implementation Details**: See `XGBOOST_IMPLEMENTATION_SUMMARY.md`
- **API Reference**: See backend code in `backend/nlu_chatbot/src/app/main.py`

## 🎓 Learning Resources

### Understanding Predictions
- Predictions use 12 historical points by default
- Model extrapolates vessel trajectory
- Includes speed and course predictions
- Haversine distance features capture spatial patterns

### Improving Accuracy
- Use more historical points (increase sequence_length)
- Ensure vessel has consistent movement patterns
- Monitor prediction vs actual positions
- Retrain model with new data periodically

## 💡 Tips & Tricks

1. **Batch Predictions**: Select multiple vessels and compare predictions
2. **Export Data**: Download prediction results as JSON
3. **Historical Analysis**: Compare predicted vs actual positions
4. **Route Planning**: Use predictions for optimal route planning
5. **Alert System**: Set up alerts for anomalous predictions

## 🔐 Security Notes

- Model weights stay on backend (not exposed to frontend)
- Only predictions and map data are transmitted
- All API calls require authentication (in production)
- Database queries are parameterized (SQL injection safe)

## 📞 Support

For issues or questions:
1. Check troubleshooting section above
2. Review full documentation
3. Check backend logs: `backend/nlu_chatbot/src/app/main.py`
4. Check frontend logs: Browser console (F12)

---

**Happy Predicting! 🚢⚓**

