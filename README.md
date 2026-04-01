# Adaptive AI Route Optimization for Dynamic Urban Logistics

A production-ready hybrid routing system combining AI-based route optimization with real-time human (rider) feedback to improve delivery efficiency in dynamic urban environments like Erbil and Baghdad.

## 🚀 Live Demo

| Service | Status | Link |
|---------|--------|------|
| API Docs | 🔄 Coming Soon | `https://your-app.render.com/docs` |
| Frontend | 🔄 Coming Soon | `https://your-app.vercel.app` |
| Health | 🔄 Coming Soon | `https://your-app.render.com/api/v1/health` |

## Core Concept

> "AI improves only when trained with real-world human behavior"

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Leaflet)                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ Route Panel │  │  Feedback   │  │   Real-time Map        │ │
│  │             │  │    Form     │  │   - Live rider tracking│ │
│  │             │  │             │  │   - WebSocket updates  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │ WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND (v2.0)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │ Route API    │  │ Feedback API │  │  Analytics API       │ │
│  │ - Dijkstra   │  │ - Submit     │  │  - Real-time stats   │ │
│  │ - A*         │  │ - Learn      │  │  - Historical data   │ │
│  │ - Mapbox     │  │              │  │                      │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ▼                    ▼                    ▼
┌─────────────────┐  ┌───────────────┐  ┌─────────────────────┐
│  PostgreSQL     │  │   Redis       │  │   Mapbox API       │
│  (Main DB)      │  │   (Cache)     │  │   (Real Routes)    │
└─────────────────┘  └───────────────┘  └─────────────────────┘
```

## Features

### Production Features
- **Async/Await**: Full async database operations with SQLAlchemy 2.0
- **PostgreSQL Ready**: Connection pooling, proper indexing
- **Redis Caching**: Route caching for performance
- **WebSocket Support**: Real-time rider tracking and road updates
- **JWT Authentication**: Secure rider authentication
- **Rate Limiting**: API request rate limiting
- **Docker Ready**: Full containerization with Docker Compose

### Core Features
- **AI Routing Engine**: Dijkstra, A*, and K-shortest paths
- **Learning Mechanism**: Adaptive weight adjustment from feedback
- **Mapbox Integration**: Real-world road data
- **Analytics Dashboard**: Comprehensive metrics

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (for production)

### Local Development

```bash
# 1. Clone and setup
cd urban-route-optimizer

# 2. Install dependencies
pip install -r backend/requirements.txt

# 3. Set environment variables
export DATABASE_URL="sqlite:///./urban_routes.db"
export MAPBOX_API_KEY="your-mapbox-key"
export JWT_SECRET="your-secret-key"

# 4. Initialize database
python3 scripts/init_data.py

# 5. Start backend
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 6. Open frontend
open ../frontend/public/index.html
```

### Docker Deployment

```bash
# 1. Create .env file
echo "MAPBOX_API_KEY=your-key" > .env
echo "JWT_SECRET=your-secret" >> .env

# 2. Start all services
docker-compose up -d

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f backend
```

The API will be available at `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Routes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/routes/generate` | Generate AI route |
| POST | `/api/v1/routes/multiple` | Get K-shortest routes |

### Feedback
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/feedback` | Submit rider feedback |
| GET | `/api/v1/feedback` | Get feedback history |

### Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/analytics/summary` | Get analytics summary |
| GET | `/api/v1/analytics/problematic-roads` | Get problematic roads |
| GET | `/api/v1/learned-shortcuts` | Get learned shortcuts |

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register rider |
| POST | `/api/v1/auth/login` | Get JWT token |

### WebSocket
| Endpoint | Description |
|----------|-------------|
| `/ws/rider/{rider_id}` | Rider real-time connection |
| `/ws/admin` | Admin dashboard connection |

## Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| DATABASE_URL | PostgreSQL connection string | postgresql://postgres:postgres@localhost:5432/urban_routes |
| REDIS_URL | Redis connection string | redis://localhost:6379/0 |
| MAPBOX_API_KEY | Mapbox API key for real routing | - |
| JWT_SECRET | Secret key for JWT tokens | your-secret-key |
| API_RATE_LIMIT | Max requests per window | 100 |
| LOG_LEVEL | Logging level | INFO |

## Learning Algorithm

The system continuously learns from rider feedback:

```python
# When riders consistently avoid AI-preferred routes:
avoided_edges_weight *= (1 + factor)  # Increase weight (discourage)

# When riders find shortcuts:
shortcut_edges_weight *= (1 - factor)  # Decrease weight (encourage)

# Track delays to penalize problematic roads:
road.avg_delay = (old_avg * usage + new_delay) / (usage + 1)
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI, SQLAlchemy 2.0 |
| Database | PostgreSQL, Redis |
| Routing | NetworkX, Mapbox Directions API |
| Auth | JWT, Passlib |
| Frontend | React, Leaflet.js |
| Deployment | Docker, Docker Compose |

## Production Considerations

1. **Database**: Use PostgreSQL for production (SQLite for dev only)
2. **Cache**: Enable Redis for route caching in production
3. **Mapbox**: Set MAPBOX_API_KEY for real-world routing
4. **Security**: Change JWT_SECRET in production
5. **HTTPS**: Enable TLS/SSL in production

## File Structure

```
urban-route-optimizer/
├── backend/
│   ├── main.py              # FastAPI app with lifespan
│   ├── core/
│   │   ├── config.py        # Settings
│   │   └── auth.py          # JWT & rate limiting
│   ├── database/
│   │   └── database.py      # Async DB setup
│   ├── models/
│   │   ├── models.py        # SQLAlchemy models
│   │   └── schemas.py       # Pydantic schemas
│   ├── routers/
│   │   └── routes.py        # API endpoints
│   └── services/
│       ├── routing_engine.py     # Dijkstra/A* + Learning
│       ├── mapbox_service.py     # Mapbox API
│       └── websocket_manager.py  # Real-time updates
├── frontend/
│   └── public/
│       └── index.html      # React SPA
├── scripts/
│   ├── init_data.py        # Erbil city data
│   └── demo_riders.py      # Demo simulation
├── docker-compose.yml      # Full stack deployment
├── Dockerfile              # Backend container
└── README.md
```

## License

MIT
