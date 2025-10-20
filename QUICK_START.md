# Maritime Defense Dashboard - Quick Start

## 🚀 Start the System (2 Steps)

### Step 1: Start Backend (Terminal 1)
```bash
cd backend/nlu_chatbot/src/app
uvicorn main:app --reload
```
✅ Backend running on `http://127.0.0.1:8000`

### Step 2: Start Frontend (Terminal 2)
```bash
cd backend/nlu_chatbot/frontend
streamlit run app.py
```
✅ Frontend running on `http://localhost:8501`

---

## 🔐 Login Credentials

### Admin Account (Pre-created)
```
Email: amansah1717@gmail.com
Password: maritime_defense_2025
```

### Create New Account
1. Go to `http://localhost:8501/Authentication`
2. Click "📝 Register" tab
3. Fill in:
   - Full Name
   - Email
   - Password (8+ chars, uppercase, digit)
   - Confirm Password
4. Click "📝 Register"
5. Login with new credentials

---

## 📍 Navigation

### Main Pages
- **Chat** - Main chat interface (`http://localhost:8501`)
- **Authentication** - Login/Register (`http://localhost:8501/Authentication`)
- **Dashboard** - Vessel tracking (`http://localhost:8501/Vessel_Tracking_&_Map_Visualization`)
- **Admin Panel** - User management (`http://localhost:8501/Admin_Panel`)

---

## 🎯 Using the Dashboard

### 1. Login
- Go to Authentication page
- Enter email and password
- Click "🔓 Login"

### 2. Query Vessel
- Go to Dashboard
- Use sidebar search to find vessel
- Click "🎯 Quick Query Selected"
- Or enter query manually

### 3. View Results
- **Map Tab**: Interactive Folium map with track
- **Time Series Tab**: Speed, course, position plots
- **Statistics Tab**: Track statistics
- **Raw Data Tab**: Complete track data

### 4. Export Data
- Click "📥 Download as CSV" or "📥 Download as JSON"
- Data saved to your computer

---

## 👥 Admin Panel

### Access
- Login as admin
- Go to `http://localhost:8501/Admin_Panel`

### Features
- View all users
- Search by email
- Activate/deactivate accounts
- View login history
- Export user data
- System statistics

---

## 🔧 Database

### Location
```
backend/nlu_chatbot/frontend/users.db
```

### Tables
- `users` - User accounts
- `login_history` - Login tracking
- `audit_log` - Action logging

### Reset Database
```bash
# Delete database (will recreate on next run)
rm backend/nlu_chatbot/frontend/users.db
```

---

## 🧪 Test Authentication

```bash
cd backend/nlu_chatbot/frontend
python test_auth_flow.py
```

Expected output:
```
✅ ALL TESTS PASSED - AUTHENTICATION SYSTEM WORKING
```

---

## 🐛 Troubleshooting

### "Invalid email or password"
- Check email spelling
- Verify password (8+ chars, uppercase, digit)
- Try registering new account

### "Cannot connect to backend"
- Ensure backend is running on port 8000
- Check: `curl http://127.0.0.1:8000/health`

### "Session not persisting"
- Clear browser cache
- Restart Streamlit (Ctrl+C and rerun)

### "Admin user not found"
- Database auto-creates admin on first run
- Check: `python test_auth_flow.py`

---

## 📊 Features

✅ **User Registration** - Email + password (8+ chars)  
✅ **JWT Authentication** - 24-hour token expiry  
✅ **Session Persistence** - Remembers login across reloads  
✅ **Admin Panel** - User management  
✅ **Vessel Tracking** - Interactive maps  
✅ **Time Series** - Speed, course, position plots  
✅ **Data Export** - CSV and JSON  
✅ **Audit Logging** - Track all actions  

---

## 🎨 Color Scheme

- **Navy Blue** (#001F3F) - Primary background
- **Steel Gray** (#2C3E50) - Secondary background
- **Neon Cyan** (#00D9FF) - Accents and highlights
- **Green** (#00CC44) - Active status
- **Orange** (#FF9900) - Warnings
- **Red** (#FF4444) - Alerts

---

## 📱 Responsive Design

Works on:
- ✅ Desktop (1920x1080+)
- ✅ Laptop (1366x768)
- ✅ Tablet (768x1024)
- ✅ Mobile (responsive)

---

## 🔒 Security

- ✅ Password hashing (SHA-256)
- ✅ Email validation
- ✅ JWT tokens
- ✅ Session management
- ✅ Audit logging
- ✅ Account deactivation

---

## 📞 Support

### Common Issues

**Q: How do I reset my password?**
A: Delete account and register new one (future: password reset feature)

**Q: Can I have multiple admin accounts?**
A: Yes, use Admin Panel to change user role to admin

**Q: How do I backup the database?**
A: Copy `frontend/users.db` to backup location

**Q: Can I delete a user?**
A: Use Admin Panel to deactivate (soft delete)

---

## 🚀 Next Steps

1. ✅ Start backend and frontend
2. ✅ Login with admin credentials
3. ✅ Explore dashboard
4. ✅ Query vessels
5. ✅ View maps and statistics
6. ✅ Export data
7. ✅ Create new user accounts
8. ✅ Manage users in admin panel

---

**Status:** 🚀 **PRODUCTION READY**  
**Version:** 1.0  
**Last Updated:** 2025-10-21

