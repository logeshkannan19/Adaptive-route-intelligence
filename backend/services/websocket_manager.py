from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, List, Set
import json
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {
            "rider": set(),
            "admin": set(),
            "analytics": set()
        }
        self.rider_locations: Dict[str, Dict] = {}
        self.road_updates: List[Dict] = []
    
    async def connect(self, websocket: WebSocket, client_type: str):
        await websocket.accept()
        self.active_connections[client_type].add(websocket)
        logger.info(f"Client connected: {client_type}, total: {len(self.active_connections[client_type])}")
    
    def disconnect(self, websocket: WebSocket, client_type: str):
        self.active_connections[client_type].discard(websocket)
        
        rider_id = None
        for rid, loc in self.rider_locations.items():
            if loc.get("websocket") == websocket:
                rider_id = rid
                break
        
        if rider_id:
            del self.rider_locations[rider_id]
        
        logger.info(f"Client disconnected: {client_type}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Error sending message: {e}")
    
    async def broadcast(self, message: dict, client_type: str = None):
        if client_type:
            connections = self.active_connections.get(client_type, set())
        else:
            connections = set()
            for conn_set in self.active_connections.values():
                connections.update(conn_set)
        
        disconnected = set()
        for connection in connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Broadcast error: {e}")
                disconnected.add(connection)
        
        for conn in disconnected:
            for conn_set in self.active_connections.values():
                conn_set.discard(conn)
    
    async def broadcast_road_update(self, road_id: int, status: str, location: Dict = None):
        message = {
            "type": "road_update",
            "data": {
                "road_id": road_id,
                "status": status,
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message, "admin")
        await self.broadcast(message, "rider")
        
        self.road_updates.append(message["data"])
        if len(self.road_updates) > 100:
            self.road_updates = self.road_updates[-100:]
    
    async def broadcast_rider_location(self, rider_id: str, location: Dict):
        self.rider_locations[rider_id] = location
        
        message = {
            "type": "rider_location",
            "data": {
                "rider_id": rider_id,
                "location": location,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message, "admin")
        await self.broadcast(message, "analytics")
    
    async def broadcast_route_update(self, route_id: int, status: str, progress: float = 0):
        message = {
            "type": "route_update",
            "data": {
                "route_id": route_id,
                "status": status,
                "progress": progress,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        await self.broadcast(message, "analytics")
    
    def get_active_riders(self) -> List[Dict]:
        return [
            {"rider_id": rid, "location": loc}
            for rid, loc in self.rider_locations.items()
        ]
    
    def get_recent_road_updates(self, limit: int = 10) -> List[Dict]:
        return self.road_updates[-limit:]


manager = ConnectionManager()


async def handle_rider_websocket(websocket: WebSocket, rider_id: str):
    await manager.connect(websocket, "rider")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "location_update":
                await manager.broadcast_rider_location(rider_id, {
                    "latitude": message.get("latitude"),
                    "longitude": message.get("longitude"),
                    "heading": message.get("heading", 0),
                    "speed": message.get("speed", 0),
                    "websocket": websocket
                })
            
            elif message.get("type") == "route_status":
                await manager.broadcast_route_update(
                    message.get("route_id"),
                    message.get("status"),
                    message.get("progress", 0)
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "rider")


async def handle_admin_websocket(websocket: WebSocket):
    await manager.connect(websocket, "admin")
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_active_riders":
                await manager.send_personal_message({
                    "type": "active_riders",
                    "data": manager.get_active_riders()
                }, websocket)
            
            elif message.get("type") == "get_road_updates":
                await manager.send_personal_message({
                    "type": "road_updates",
                    "data": manager.get_recent_road_updates()
                }, websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "admin")
