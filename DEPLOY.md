# Quick Deployment Guide

## Option 1: Render (Backend + PostgreSQL - Free)

```bash
# 1. Push code to GitHub (already done)
# 2. Go to https://render.com
# 3. Create new Web Service
# 4. Connect your GitHub repository
# 5. Settings:
#    - Build Command: pip install -r backend/requirements.txt
#    - Start Command: uvicorn backend.main:app --host 0.0.0.0 --port 10000
# 6. Add Environment Variables:
#    - DATABASE_URL: postgresql://... (create via Render)
#    - MAPBOX_API_KEY: your-key
```

## Option 2: Railway (Full Stack)

```bash
# 1. Go to https://railway.app
# 2. Connect GitHub repository
# 3. Add PostgreSQL plugin
# 4. Deploy automatically
```

## Option 3: Fly.io (Docker)

```bash
# 1. Install flyctl
# 2. fly launch
# 3. fly deploy
```

## Option 4: Vercel (Frontend only)

```bash
# 1. Go to https://vercel.com
# 2. Import GitHub repo
# 3. Set output directory to frontend/public
# 4. Deploy
```

## Recommended: Render Free Tier

| Service | Free Tier |
|----------|-----------|
| Backend | 750 hours/month |
| PostgreSQL | 1GB storage |
| Bandwidth | 1GB/month |

## Environment Variables to Set

```
DATABASE_URL=postgresql://user:pass@host:5432/db
MAPBOX_API_KEY=your_mapbox_token
JWT_SECRET=random_secret_key
LOG_LEVEL=INFO
```

## After Deployment

Update frontend API URL in `frontend/public/index.html`:
```javascript
const API_URL = 'https://your-backend.render.com/api/v1';
```
