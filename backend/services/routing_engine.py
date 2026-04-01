import networkx as nx
import asyncio
from typing import List, Dict, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
import math
import json

from models.models import Location, Road, RiderFeedback
from core.config import settings


class RoutingEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.graph = nx.DiGraph()
        self.location_cache: Dict[int, Dict] = {}
    
    async def build_graph(self):
        result = await self.db.execute(select(Location).where(Location.is_active == True))
        locations = result.scalars().all()
        
        for loc in locations:
            self.location_cache[loc.id] = {
                "id": loc.id,
                "name": loc.name,
                "lat": loc.latitude,
                "lng": loc.longitude,
                "type": loc.location_type
            }
            self.graph.add_node(
                loc.id,
                name=loc.name,
                lat=loc.latitude,
                lng=loc.longitude,
                type=loc.location_type
            )
        
        result = await self.db.execute(
            select(Road).where(Road.road_status != "blocked")
        )
        roads = result.scalars().all()
        
        for road in roads:
            if self._is_road_available(road):
                weight = await self._calculate_edge_weight(road)
                self.graph.add_edge(
                    road.source_id,
                    road.target_id,
                    road_id=road.id,
                    distance=road.distance_km,
                    weight=weight,
                    base_weight=road.base_weight,
                    current_weight=road.current_weight,
                    status=road.road_status,
                    flood_prone=road.is_flood_prone,
                    road_type=road.road_type,
                    max_speed=road.max_speed_kmh
                )
    
    def _is_road_available(self, road: Road) -> bool:
        current_hour = datetime.now().hour
        
        if road.blocked_after_hour and current_hour >= road.blocked_after_hour:
            return False
        
        return True
    
    async def _calculate_edge_weight(self, road: Road) -> float:
        weight = road.distance_km * road.current_weight
        
        if road.road_status == "risky":
            weight *= 2.0
        elif road.road_status == "flooded":
            weight *= 5.0
        
        if road.is_flood_prone:
            weight *= 1.5
        
        if road.avg_delay_minutes > 0:
            weight += road.avg_delay_minutes * 0.1
        
        speed_factor = 50 / max(road.max_speed_kmh, 1)
        weight *= speed_factor
        
        return weight
    
    async def recalculate_weights(self):
        result = await self.db.execute(select(Road))
        roads = result.scalars().all()
        
        for u, v, data in self.graph.edges(data=True):
            road_id = data.get("road_id")
            road = next((r for r in roads if r.id == road_id), None)
            if road:
                data["weight"] = await self._calculate_edge_weight(road)
                data["current_weight"] = road.current_weight
    
    async def dijkstra_route(self, start_id: int, end_id: int) -> Optional[List[int]]:
        try:
            if not self.graph.has_node(start_id) or not self.graph.has_node(end_id):
                return None
            path = nx.dijkstra_path(self.graph, start_id, end_id, weight="weight")
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    async def astar_route(self, start_id: int, end_id: int) -> Optional[List[int]]:
        try:
            if not self.graph.has_node(start_id) or not self.graph.has_node(end_id):
                return None
            
            heuristic = lambda n1, n2: self._haversine_distance(
                self.location_cache.get(n1, {}).get("lat", 0),
                self.location_cache.get(n1, {}).get("lng", 0),
                self.location_cache.get(n2, {}).get("lat", 0),
                self.location_cache.get(n2, {}).get("lng", 0)
            )
            path = nx.astar_path(self.graph, start_id, end_id, heuristic=heuristic, weight="weight")
            return path
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
    
    async def k_shortest_paths(self, start_id: int, end_id: int, k: int = 3) -> List[List[int]]:
        try:
            if not self.graph.has_node(start_id) or not self.graph.has_node(end_id):
                return []
            return list(nx.shortest_simple_paths(self.graph, start_id, end_id, weight="weight"))[:k]
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.asin(math.sqrt(a))
    
    async def get_route_details(self, path: List[int]) -> Dict:
        if not path:
            return {}
        
        total_distance = 0
        total_weight = 0
        edges_info = []
        
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_data = self.graph.get_edge_data(u, v)
            if edge_data:
                total_distance += edge_data.get("distance", 0)
                total_weight += edge_data.get("weight", 0)
                edges_info.append({
                    "from": u,
                    "to": v,
                    "from_name": self.location_cache.get(u, {}).get("name", ""),
                    "to_name": self.location_cache.get(v, {}).get("name", ""),
                    "distance": edge_data.get("distance"),
                    "weight": edge_data.get("weight"),
                    "status": edge_data.get("status"),
                    "road_type": edge_data.get("road_type")
                })
        
        avg_speed_kmh = 30
        estimated_time = (total_distance / avg_speed_kmh) * 60
        
        return {
            "path": path,
            "path_names": [self.location_cache.get(n, {}).get("name", "") for n in path],
            "total_distance_km": round(total_distance, 2),
            "estimated_time_minutes": round(estimated_time, 2),
            "total_weight": round(total_weight, 2),
            "edges": edges_info
        }
    
    async def get_neighbors(self, node_id: int) -> List[Dict]:
        neighbors = []
        for successor in self.graph.successors(node_id):
            edge_data = self.graph.get_edge_data(node_id, successor)
            neighbors.append({
                "node_id": successor,
                "name": self.location_cache.get(successor, {}).get("name", ""),
                "distance": edge_data.get("distance", 0),
                "weight": edge_data.get("weight", 0),
                "status": edge_data.get("status", "open")
            })
        return neighbors


class LearningEngine:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.deviation_threshold = 2
        self.weight_adjustment_factor = 0.15
        self.shortcut_bonus = 0.2
        self.penalty_factor = 0.25
        self.min_weight = 0.1
        self.max_weight = 5.0
    
    async def process_feedback(self, feedback: RiderFeedback):
        if not feedback.ai_route_path or not feedback.actual_route_path:
            return
        
        ai_path_set = set(zip(feedback.ai_route_path[:-1], feedback.ai_route_path[1:]))
        actual_path_set = set(zip(feedback.actual_route_path[:-1], feedback.actual_route_path[1:]))
        
        avoided_edges = ai_path_set - actual_path_set
        preferred_edges = actual_path_set - ai_path_set
        
        deviation_count = len(feedback.actual_route_path) - len(feedback.ai_route_path)
        
        adjustment_factor = self.weight_adjustment_factor * (1 + abs(deviation_count) * 0.1)
        
        for edge in avoided_edges:
            await self._adjust_edge_weight(edge[0], edge[1], adjustment_factor, increase=True)
        
        for edge in preferred_edges:
            await self._adjust_edge_weight(edge[0], edge[1], adjustment_factor, increase=False)
        
        if feedback.shortcut_used:
            await self._apply_shortcut_bonus(feedback.actual_route_path)
        
        if feedback.delay_minutes > 5:
            await self._learn_from_delay(feedback.ai_route_path, feedback.delay_minutes)
        
        await self._normalize_weights()
    
    async def _adjust_edge_weight(self, source_id: int, target_id: int, factor: float, increase: bool):
        result = await self.db.execute(
            select(Road).where(
                Road.source_id == source_id,
                Road.target_id == target_id
            )
        )
        road = result.scalar_one_or_none()
        
        if road:
            if increase:
                new_weight = min(self.max_weight, road.current_weight * (1 + factor))
            else:
                new_weight = max(self.min_weight, road.current_weight * (1 - factor))
            
            await self.db.execute(
                update(Road)
                .where(Road.id == road.id)
                .values(current_weight=new_weight, updated_at=datetime.utcnow())
            )
    
    async def _apply_shortcut_bonus(self, path: List[int]):
        for i in range(len(path) - 1):
            await self._adjust_edge_weight(
                path[i], path[i + 1],
                self.shortcut_bonus,
                increase=False
            )
    
    async def _learn_from_delay(self, ai_path: List[int], delay: float):
        for i in range(len(ai_path) - 1):
            result = await self.db.execute(
                select(Road).where(
                    Road.source_id == ai_path[i],
                    Road.target_id == ai_path[i + 1]
                )
            )
            road = result.scalar_one_or_none()
            
            if road:
                new_avg_delay = (road.avg_delay_minutes * road.usage_count + delay) / (road.usage_count + 1)
                await self.db.execute(
                    update(Road)
                    .where(Road.id == road.id)
                    .values(
                        avg_delay_minutes=new_avg_delay,
                        usage_count=road.usage_count + 1
                    )
                )
    
    async def _normalize_weights(self):
        result = await self.db.execute(select(Road))
        roads = result.scalars().all()
        
        for road in roads:
            if road.current_weight < road.base_weight:
                road.current_weight = min(road.base_weight, road.current_weight * 1.005)
            elif road.current_weight > road.base_weight:
                road.current_weight = max(road.base_weight, road.current_weight * 0.995)
        
        await self.db.commit()
    
    async def get_learned_shortcuts(self) -> List[Dict]:
        result = await self.db.execute(
            select(Road).where(
                Road.current_weight < Road.base_weight * 0.7
            ).order_by(Road.current_weight)
        )
        roads = result.scalars().all()
        
        return [
            {
                "road_id": r.id,
                "source_id": r.source_id,
                "target_id": r.target_id,
                "weight_reduction": round(1 - (r.current_weight / r.base_weight), 2),
                "avg_delay": r.avg_delay_minutes
            }
            for r in roads
        ]
    
    async def get_problematic_roads(self) -> List[Dict]:
        result = await self.db.execute(
            select(Road).where(
                Road.current_weight > Road.base_weight * 1.5
            ).order_by(Road.current_weight.desc())
        )
        roads = result.scalars().all()
        
        return [
            {
                "road_id": r.id,
                "source_id": r.source_id,
                "target_id": r.target_id,
                "weight_increase": round((r.current_weight / r.base_weight - 1) * 100, 1),
                "avg_delay": r.avg_delay_minutes,
                "status": r.road_status
            }
            for r in roads
        ]
