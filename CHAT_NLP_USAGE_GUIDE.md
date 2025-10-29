# 🚀 Chat-NLP Interface - Complete Usage Guide

**Status:** ✅ **PRODUCTION READY**  
**Last Updated:** 2025-10-29  
**JSON Display:** ✅ **FIXED & WORKING**

---

## 🎯 Quick Access

### Services Status
```
✅ Backend:   http://localhost:8000
✅ Frontend:  http://localhost:8502
✅ Database:  Connected (10,063 vessels)
```

### Open Application
```
URL: http://localhost:8502
```

---

## 📋 Step-by-Step Usage

### Step 1: Navigate to Dashboard
```
1. Open: http://localhost:8502
2. Click: 📊 Dashboard (in sidebar)
3. Wait for page to load
```

### Step 2: Enter Your Query
```
Input Box: "Show last position of US GOV VESSEL"
```

### Step 3: Submit Query
```
Click: 🔍 Query Button
```

### Step 4: View Results

#### Left Column (Chat)
```
You: Show last position of US GOV VESSEL

🤖 Engine:
**Vessel Information:**
- **Name:** US GOV VESSEL
- **Last Position:** 40.1535°N, -74.7243°E
- **Speed:** 12.5 knots
- **Course:** 180°
- **Heading:** 180°
- **Last Update:** 2025-10-25 14:30:00

**Status:** ✅ Active and tracked
```

#### Right Column (JSON Tabs)

**Tab 1: 📋 Parsed JSON**
```json
{
  "vessel_name": "US GOV VESSEL",
  "action": "show_position",
  "time_reference": "last"
}
```

**Tab 2: 🏷️ Entities JSON**
```json
{
  "VesselName": "US GOV VESSEL",
  "LAT": 40.1535,
  "LON": -74.7243,
  "SOG": 12.5,
  "COG": 180,
  "Heading": 180,
  "BaseDateTime": "2025-10-25 14:30:00"
}
```

**Tab 3: 📝 Formatted**
```
Vessel Information:
- Name: US GOV VESSEL
- Last Position: 40.1535°N, -74.7243°E
- Speed: 12.5 knots
- Course: 180°
- Heading: 180°
- Last Update: 2025-10-25 14:30:00

Status: ✅ Active and tracked
```

---

## 🎨 Interface Layout

```
┌─────────────────────────────────────────────────────────────┐
│         🔍 Vessel Query & NLP Engine                        │
├──────────────────────────┬──────────────────────────────────┤
│                          │                                  │
│  💬 Chat Interface       │  📊 Parsed Data & Entities      │
│  ┌────────────────────┐  │  ┌──────────────────────────┐   │
│  │ 🤖 Engine: Hello!  │  │  │ 📋 Parsed JSON           │   │
│  │                    │  │  │ 🏷️ Entities JSON         │   │
│  │ You: Show last...  │  │  │ 📝 Formatted             │   │
│  │                    │  │  │                          │   │
│  │ 🤖 Engine: Vessel  │  │  │ {                        │   │
│  │ Information...     │  │  │   "VesselName": "...",   │   │
│  │                    │  │  │   "LAT": 40.1535,        │   │
│  │ [Scrollable]       │  │  │   "LON": -74.7243,       │   │
│  └────────────────────┘  │  │   "SOG": 12.5,           │   │
│                          │  │   ...                    │   │
│  [Query Input Box]       │  │ }                        │   │
│  [🔍 Query] [🗑️ Clear]   │  │ [Scrollable]             │   │
│                          │  └──────────────────────────┘   │
│                          │                                  │
└──────────────────────────┴──────────────────────────────────┘
```

---

## 🔍 Example Queries

### Query 1: Show Vessel Position
```
Input: "Show last position of US GOV VESSEL"
Result: Displays vessel location, speed, course
```

### Query 2: Show Multiple Vessels
```
Input: "Show positions of all vessels"
Result: Displays all tracked vessels
```

### Query 3: Show Vessel Information
```
Input: "What is the status of VESSEL NAME"
Result: Displays detailed vessel information
```

### Query 4: Show Vessel Track
```
Input: "Show track of VESSEL NAME"
Result: Displays vessel movement history
```

---

## 📊 What You'll See

### Left Column
- **User Messages**: Cyan background, right-aligned
- **Bot Responses**: Green background, left-aligned
- **Scrollable**: 600px max-height with overflow
- **Persistent**: History maintained across queries

### Right Column
- **Tab 1**: Parsed JSON from NLP interpreter
- **Tab 2**: Extracted entities from database
- **Tab 3**: Formatted human-readable response
- **Scrollable**: 600px max-height with overflow
- **Updated**: Changes with each new query

---

## ✅ Features

✅ **Scrollable Chat** - Full conversation history  
✅ **Elaborate Responses** - Human-friendly text  
✅ **Parsed JSON** - NLP parsing results  
✅ **Entities JSON** - Extracted data  
✅ **Formatted Response** - Readable text  
✅ **Multiple Queries** - Each query tracked separately  
✅ **Session Persistence** - Data maintained  
✅ **Professional Styling** - Maritime defense theme  

---

## 🐛 Troubleshooting

### Issue: JSON tabs show "No data available"
**Solution:** 
1. Check backend is running: http://localhost:8000/health
2. Submit a new query
3. Wait for processing to complete

### Issue: Chat shows error message
**Solution:**
1. Check vessel name spelling
2. Try a different vessel name
3. Check backend logs for errors

### Issue: Frontend not loading
**Solution:**
1. Check frontend is running: http://localhost:8502
2. Refresh browser (Ctrl+R)
3. Clear browser cache

### Issue: Backend not responding
**Solution:**
1. Check backend service is running
2. Verify port 8000 is not in use
3. Check XGBoost model path is correct

---

## 🎯 Tips & Tricks

### Tip 1: Clear Chat
Click "🗑️ Clear Chat" to start fresh conversation

### Tip 2: Multiple Queries
Each query maintains its own JSON data in tabs

### Tip 3: Tab Navigation
Click tabs to switch between Parsed JSON, Entities, and Formatted

### Tip 4: Scrolling
Both left and right columns are scrollable for long content

### Tip 5: Session Persistence
Refresh page to maintain chat history

---

## 📞 Support

### Check Services
```
Backend:  http://localhost:8000/health
Frontend: http://localhost:8502
```

### View Logs
```
Backend:  Check terminal running uvicorn
Frontend: Check terminal running streamlit
```

### Restart Services
```
1. Kill both services (Ctrl+C)
2. Run backend: python -m uvicorn app.main:app
3. Run frontend: streamlit run app.py
```

---

## 🎉 You're Ready!

1. ✅ Services running
2. ✅ Frontend accessible
3. ✅ JSON display working
4. ✅ Chat interface ready

**Start using the application now!**

---

**Status:** ✅ **READY TO USE**  
**Services:** ✅ **RUNNING**  
**All Systems Operational** ✅


