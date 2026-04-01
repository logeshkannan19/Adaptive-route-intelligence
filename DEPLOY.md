# Deployment Instructions

## 🚀 Quick Deploy (5 minutes)

### Backend - Render (Free Tier)
1. Go to **https://render.com** → Sign up with GitHub
2. Create New → **Web Service**
3. Connect repository: `logeshkannan19/Adaptive-route-intelligence`
4. Settings:
   - Build Command: `pip install -r backend/requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Environment Variables:
   ```
   DATABASE_URL=sqlite:///./urban_routes.db
   MAPBOX_API_KEY=
   JWT_SECRET=your-secret-key-change-in-production
   ```
6. Deploy

### Frontend - Vercel (Free Tier)
1. Go to **https://vercel.com** → Sign up with GitHub
2. Import repository: `logeshkannan19/Adaptive-route-intelligence`
3. Settings:
   - Framework Preset: `Other`
   - Build Command: (leave empty)
   - Output Directory: `frontend/public`
4. Deploy

### Update Frontend API URL
After backend deploys, edit `frontend/public/index.html`:
```javascript
const API_URL = 'https://your-backend.onrender.com/api/v1';
```
Then redeploy frontend.

---

## 🔧 Alternative: Quick Test Deploy

### Use ngrok + Localhost
```bash
# 1. Start backend locally
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# 2. Install ngrok
ngrok http 8000

# 3. Use the ngrok URL for frontend
```

### Use Replit (Instant)
1. Go to **https://replit.com**
2. Import GitHub repo
3. Run backend in Shell: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
4. Use the provided URL

---

## 📋 Post-Deploy Checklist

- [ ] Backend running at `https://xxx.onrender.com`
- [ ] Frontend running at `https://xxx.vercel.app`
- [ ] API docs at `/docs`
- [ ] Database initialized with `python scripts/init_data.py`
- [ ] Mapbox API key added (optional - for real routing)

## 🔗 Live Demo (After Deploy)

| Service | URL |
|---------|-----|
| API Docs | `https://your-app.render.com/docs` |
| Health | `https://your-app.render.com/api/v1/health` |
| Frontend | `https://your-app.vercel.app` |
