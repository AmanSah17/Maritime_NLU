# Maritime Defense Dashboard - Quick Setup Guide

**Status:** ✅ **READY TO DEPLOY**

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd backend/nlu_chatbot
pip install plotly kaleido
```

### Step 2: Start Backend
```bash
cd backend/nlu_chatbot/src/app
uvicorn main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Step 3: Start Frontend (New Terminal)
```bash
cd backend/nlu_chatbot/frontend
streamlit run app.py
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 4: Access Dashboard
1. Open browser: `http://localhost:8501`
2. Navigate to: "Vessel Tracking & Map Visualization"
3. Login with:
   - Username: `admin`
   - Password: `maritime_defense_2025`

### Step 5: Query a Vessel
1. In sidebar, search for vessel (e.g., "LAVACA")
2. Click "🎯 Quick Query Selected"
3. View results in dashboard tabs

---

## 📋 What's New

### ✨ New Features

1. **JWT Authentication**
   - Secure login system
   - 24-hour token expiration
   - Session persistence

2. **Time Series Dashboard**
   - Speed (SOG) plots
   - Position (LAT/LON) plots
   - Course & Heading plots
   - Real-time statistics

3. **Defense Styling**
   - Navy Blue (#001F3F)
   - Steel Gray (#2C3E50)
   - Neon Cyan (#00D9FF)
   - Monospace fonts
   - Glow effects

4. **Interactive Maps**
   - Color-coded markers
   - Movement arrows
   - Ship icons
   - Polyline tracks

5. **Session Management**
   - Remembers selected vessel
   - Saves track data
   - Tracks interactions
   - Persists preferences

6. **Data Export**
   - CSV export
   - JSON export
   - Formatted data

---

## 🔐 Login Credentials

### Admin Account
```
Username: admin
Password: maritime_defense_2025
```

### Operator Account
```
Username: operator
Password: operator_2025
```

---

## 📊 Dashboard Tabs

### 1. 🗺️ Interactive Map
- Folium map with vessel track
- Green (recent) → Blue (middle) → Red (old)
- Movement arrows
- Zoom and pan controls

### 2. 📈 Time Series
- Speed Over Ground (SOG)
- Position over time
- Course & Heading
- Latitude & Longitude

### 3. 📊 Statistics
- Total track points
- Speed statistics
- Course information
- Position range

### 4. 📋 Raw Data
- Complete track table
- CSV download
- JSON download

---

## 🎨 Color Scheme

| Element | Color | Hex |
|---------|-------|-----|
| Background | Navy Blue | #001F3F |
| Secondary | Steel Gray | #2C3E50 |
| Accent | Neon Cyan | #00D9FF |
| Success | Green | #00CC44 |
| Warning | Orange | #FF9900 |
| Alert | Red | #FF4444 |

---

## 🔧 Configuration

### JWT Settings
**File:** `auth_manager.py`
```python
SECRET_KEY = "maritime_defense_secret_2025"
TOKEN_EXPIRY = 24  # hours
```

### User Preferences
**File:** `auth_manager.py`
```python
{
    "theme": "defense",
    "auto_refresh": True,
    "refresh_interval": 30,
    "map_zoom": 12,
    "show_track_arrows": True,
    "show_statistics": True
}
```

---

## 📁 New Files Created

```
frontend/
├── auth_manager.py                 # JWT & session management
├── styles/
│   └── maritime_defense.css       # Defense styling
├── js/
│   └── maritime_dashboard.js      # Interactive features
└── pages/
    └── show_dataframes.py         # Updated dashboard
```

---

## 🧪 Testing

### Test 1: Authentication
1. Go to dashboard
2. Try login with wrong credentials → Should fail
3. Login with correct credentials → Should succeed
4. Refresh page → Should stay logged in

### Test 2: Vessel Query
1. Search for vessel in sidebar
2. Click "Quick Query Selected"
3. Should see track data in tabs

### Test 3: Time Series
1. Click "📈 Time Series" tab
2. Should see 4 interactive plots
3. Hover over plots to see values

### Test 4: Statistics
1. Click "📊 Statistics" tab
2. Should see 7 metric cards
3. Values should match track data

### Test 5: Data Export
1. Click "📋 Raw Data" tab
2. Click "📥 Download as CSV"
3. File should download
4. Click "📥 Download as JSON"
5. File should download

---

## 🐛 Common Issues

### Issue: "ModuleNotFoundError: No module named 'plotly'"
**Solution:**
```bash
pip install plotly kaleido
```

### Issue: "Cannot connect to backend"
**Solution:**
1. Verify backend is running on port 8000
2. Check firewall settings
3. Try: `curl http://127.0.0.1:8000/health`

### Issue: "Login not working"
**Solution:**
1. Check credentials (case-sensitive)
2. Verify auth_manager.py is in frontend folder
3. Check browser console for errors

### Issue: "Maps not loading"
**Solution:**
1. Verify track data is returned
2. Check browser console for errors
3. Try refreshing page

### Issue: "Plots not displaying"
**Solution:**
1. Ensure plotly is installed
2. Check browser console for errors
3. Try different browser

---

## 📊 Performance Tips

1. **Faster Queries:** Use vessel name search instead of full list
2. **Smoother Maps:** Limit track data to last 100 points
3. **Better Performance:** Close unused tabs
4. **Faster Rendering:** Use Chrome/Edge instead of Firefox

---

## 🔄 Session Persistence

### How It Works
1. Login creates JWT token
2. Token stored in session state
3. Page reload restores session
4. Token verified on each action
5. Logout clears session

### Session Data Saved
- Authentication token
- Selected vessel
- Track data
- User preferences
- Interaction history

---

## 📈 Next Steps

1. ✅ Start backend and frontend
2. ✅ Login to dashboard
3. ✅ Query a vessel
4. ✅ Explore time series plots
5. ✅ Export data
6. ✅ Test session persistence

---

## 🎯 Key Features Summary

| Feature | Status | Details |
|---------|--------|---------|
| JWT Auth | ✅ | 24-hour tokens |
| Time Series | ✅ | 4 plot types |
| Maps | ✅ | Interactive Folium |
| Statistics | ✅ | Real-time metrics |
| Export | ✅ | CSV & JSON |
| Styling | ✅ | Defense theme |
| Session | ✅ | Persistent state |
| Quick Select | ✅ | Sidebar vessel search |

---

## 📞 Support

**Backend Issues:**
- Check terminal for error messages
- Verify database connection
- Check port 8000 availability

**Frontend Issues:**
- Check browser console (F12)
- Verify Streamlit is running
- Clear browser cache

**Data Issues:**
- Verify vessel exists in database
- Check track data format
- Review backend logs

---

## 🚀 Production Deployment

### Before Deploying

1. [ ] Change SECRET_KEY in auth_manager.py
2. [ ] Update admin credentials
3. [ ] Enable HTTPS
4. [ ] Configure database
5. [ ] Set up logging
6. [ ] Test all features
7. [ ] Review security

### Deployment Steps

1. Install dependencies
2. Configure environment variables
3. Start backend with production settings
4. Start frontend with production settings
5. Configure reverse proxy (nginx)
6. Set up SSL certificates
7. Monitor logs

---

## 📄 Files Modified

- ✅ `show_dataframes.py` - Enhanced with dashboard
- ✅ `auth_manager.py` - New authentication module
- ✅ `maritime_defense.css` - New styling
- ✅ `maritime_dashboard.js` - New interactivity

---

**Status:** 🚀 **READY FOR DEPLOYMENT**  
**Last Updated:** 2025-10-19  
**Version:** 1.0

