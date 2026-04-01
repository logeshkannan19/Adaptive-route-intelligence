import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/urban_routes"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40
    
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    MAPBOX_API_KEY: str = os.getenv("MAPBOX_API_KEY", "")
    MAPBOX Directions_URL: str = "https://api.mapbox.com/directions/v5/mapbox/driving"
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    
    API_RATE_LIMIT: int = 100
    API_RATE_WINDOW: int = 60
    
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
