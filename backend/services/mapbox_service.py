import httpx
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from core.config import settings
import asyncio


class MapboxService:
    def __init__(self):
        self.api_key = settings.MAPBOX_API_KEY
        self.base_url = settings.MAPBOX_Directions_URL
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def get_route(
        self,
        coordinates: List[List[float]],
        alternatives: bool = True,
        geometries: str = "geojson",
        overview: str = "full",
        annotations: bool = True
    ) -> Optional[Dict]:
        if not self.api_key:
            return None
        
        coord_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
        url = f"{self.base_url}/{coord_str}"
        
        params = {
            "access_token": self.api_key,
            "alternatives": str(alternatives).lower(),
            "geometries": geometries,
            "overview": overview,
            "annotations": "duration,distance,speed" if annotations else "false"
        }
        
        try:
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == "Ok":
                return data
            return None
        except Exception as e:
            print(f"Mapbox API error: {e}")
            return None
    
    async def get_route_between_points(
        self,
        start_lat: float,
        start_lon: float,
        end_lat: float,
        end_lon: float
    ) -> Optional[Dict]:
        return await self.get_route([[start_lat, start_lon], [end_lat, end_lon]])
    
    async def get_optimized_route(
        self,
        waypoints: List[Dict[str, float]],
        destination: str = "any"
    ) -> Optional[Dict]:
        if not self.api_key:
            return None
        
        coord_str = ";".join([f"{wp['lon']},{wp['lat']}" for wp in waypoints])
        url = f"https://api.mapbox.com/optimized-trips/v1/mapbox/driving/{coord_str}"
        
        params = {
            "access_token": self.api_key,
            "destination": destination,
            "geometries": "geojson"
        }
        
        try:
            response = await self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data
        except Exception as e:
            print(f"Mapbox optimization error: {e}")
            return None
    
    async def close(self):
        await self.session.aclose()


class RouteCacheService:
    def __init__(self):
        self.cache: Dict[str, Any] = {}
        self.cache_ttl_seconds = 300
    
    def _generate_cache_key(self, start: tuple, end: tuple) -> str:
        return f"route_{start[0]}_{start[1]}_{end[0]}_{end[1]}"
    
    def get(self, start: tuple, end: tuple) -> Optional[Dict]:
        key = self._generate_cache_key(start, end)
        entry = self.cache.get(key)
        
        if entry:
            if (datetime.utcnow() - entry["timestamp"]).total_seconds() < self.cache_ttl_seconds:
                return entry["data"]
            else:
                del self.cache[key]
        
        return None
    
    def set(self, start: tuple, end: tuple, data: Dict):
        key = self._generate_cache_key(start, end)
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.utcnow()
        }
    
    def invalidate(self, location_id: int = None):
        if location_id is None:
            self.cache.clear()
        else:
            keys_to_delete = [k for k in self.cache if str(location_id) in k]
            for key in keys_to_delete:
                del self.cache[key]
    
    def get_stats(self) -> Dict:
        total_entries = len(self.cache)
        expired = sum(
            1 for v in self.cache.values()
            if (datetime.utcnow() - v["timestamp"]).total_seconds() >= self.cache_ttl_seconds
        )
        
        return {
            "total_entries": total_entries,
            "expired_entries": expired,
            "active_entries": total_entries - expired
        }


mapbox_service = MapboxService()
route_cache = RouteCacheService()
