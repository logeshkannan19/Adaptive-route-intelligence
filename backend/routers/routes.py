from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from datetime import datetime, timedelta

from database.database import get_db
from models.schemas import (
    LocationCreate, LocationResponse,
    RoadCreate, RoadUpdate, RoadResponse,
    RouteRequest, RouteResponse, MultiRouteResponse,
    FeedbackCreate, FeedbackResponse,
    RoadConditionCreate, RoadConditionResponse,
    AnalyticsSummary, ProblematicRoadResponse,
    RiderCreate, RiderResponse, TokenResponse,
    HealthResponse
)
from models.models import Location, Road, Route, RiderFeedback, RoadConditionUpdate, Analytics, Rider
from services.routing_engine import RoutingEngine, LearningEngine
from services.mapbox_service import mapbox_service, route_cache
from services.websocket_manager import manager, handle_rider_websocket, handle_admin_websocket
from core.auth import create_access_token, get_password_hash, rate_limiter
from core.config import settings

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def root():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "database": "connected",
        "cache": "connected",
        "timestamp": datetime.utcnow()
    }


@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


@router.get("/locations", response_model=List[LocationResponse])
async def get_locations(
    city: str = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    query = select(Location)
    if city:
        query = query.where(Location.city == city)
    if active_only:
        query = query.where(Location.is_active == True)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/locations", response_model=LocationResponse)
async def create_location(location: LocationCreate, db: AsyncSession = Depends(get_db)):
    db_location = Location(**location.model_dump())
    db.add(db_location)
    await db.commit()
    await db.refresh(db_location)
    return db_location


@router.get("/roads", response_model=List[RoadResponse])
async def get_roads(
    status: str = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Road)
    if status:
        query = query.where(Road.road_status == status)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/roads", response_model=RoadResponse)
async def create_road(road: RoadCreate, db: AsyncSession = Depends(get_db)):
    db_road = Road(**road.model_dump())
    db.add(db_road)
    await db.commit()
    await db.refresh(db_road)
    return db_road


@router.patch("/roads/{road_id}", response_model=RoadResponse)
async def update_road(
    road_id: int,
    road_update: RoadUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Road).where(Road.id == road_id))
    db_road = result.scalar_one_or_none()
    
    if not db_road:
        raise HTTPException(status_code=404, detail="Road not found")
    
    update_data = road_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_road, key, value)
    
    db_road.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(db_road)
    
    await manager.broadcast_road_update(road_id, db_road.road_status)
    
    return db_road


@router.post("/routes/generate", response_model=RouteResponse)
async def generate_route(
    route_req: RouteRequest,
    db: AsyncSession = Depends(get_db)
):
    engine = RoutingEngine(db)
    await engine.build_graph()
    
    if route_req.use_mapbox and settings.MAPBOX_API_KEY:
        start_loc = await db.get(Location, route_req.start_location_id)
        end_loc = await db.get(Location, route_req.end_location_id)
        
        if start_loc and end_loc:
            mapbox_result = await mapbox_service.get_route_between_points(
                start_loc.latitude, start_loc.longitude,
                end_loc.latitude, end_loc.longitude
            )
            
            if mapbox_result and mapbox_result.get("routes"):
                route_data = mapbox_result["routes"][0]
                
                db_route = Route(
                    start_location_id=route_req.start_location_id,
                    end_location_id=route_req.end_location_id,
                    path_nodes=[],
                    total_distance=route_data["distance"] / 1000,
                    estimated_time_minutes=route_data["duration"] / 60,
                    route_type="mapbox",
                    algorithm_used="mapbox_directions"
                )
                db.add(db_route)
                await db.commit()
                await db.refresh(db_route)
                
                return RouteResponse(
                    id=db_route.id,
                    path=[],
                    path_names=[start_loc.name, end_loc.name],
                    total_distance_km=round(route_data["distance"] / 1000, 2),
                    estimated_time_minutes=round(route_data["duration"] / 60, 2),
                    total_weight=0,
                    edges=[],
                    route_type="mapbox",
                    algorithm_used="mapbox_directions",
                    created_at=db_route.created_at
                )
    
    if route_req.algorithm == "astar":
        path = await engine.astar_route(route_req.start_location_id, route_req.end_location_id)
    else:
        path = await engine.dijkstra_route(route_req.start_location_id, route_req.end_location_id)
    
    if not path:
        raise HTTPException(status_code=404, detail="No route found between locations")
    
    details = await engine.get_route_details(path)
    
    db_route = Route(
        start_location_id=route_req.start_location_id,
        end_location_id=route_req.end_location_id,
        path_nodes=path,
        total_distance=details["total_distance_km"],
        estimated_time_minutes=details["estimated_time_minutes"],
        route_type="ai_generated",
        algorithm_used=route_req.algorithm
    )
    db.add(db_route)
    await db.commit()
    await db.refresh(db_route)
    
    return RouteResponse(
        id=db_route.id,
        path=details["path"],
        path_names=details["path_names"],
        total_distance_km=details["total_distance_km"],
        estimated_time_minutes=details["estimated_time_minutes"],
        total_weight=details["total_weight"],
        edges=details["edges"],
        route_type="ai_generated",
        algorithm_used=route_req.algorithm,
        created_at=db_route.created_at
    )


@router.post("/routes/multiple", response_model=MultiRouteResponse)
async def get_multiple_routes(
    route_req: RouteRequest,
    k: int = 3,
    db: AsyncSession = Depends(get_db)
):
    engine = RoutingEngine(db)
    await engine.build_graph()
    
    paths = await engine.k_shortest_paths(route_req.start_location_id, route_req.end_location_id, k)
    
    routes = []
    for path in paths:
        details = await engine.get_route_details(path)
        routes.append(RouteResponse(
            path=details["path"],
            path_names=details["path_names"],
            total_distance_km=details["total_distance_km"],
            estimated_time_minutes=details["estimated_time_minutes"],
            total_weight=details["total_weight"],
            edges=details["edges"],
            route_type="ai_generated",
            algorithm_used=f"k_shortest_{route_req.algorithm}"
        ))
    
    return MultiRouteResponse(routes=routes, alternatives=len(routes))


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(feedback: FeedbackCreate, db: AsyncSession = Depends(get_db)):
    db_feedback = RiderFeedback(**feedback.model_dump())
    db.add(db_feedback)
    await db.flush()
    
    learning_engine = LearningEngine(db)
    await learning_engine.process_feedback(db_feedback)
    
    await db.commit()
    await db.refresh(db_feedback)
    
    return db_feedback


@router.get("/feedback", response_model=List[FeedbackResponse])
async def get_feedback(
    rider_id: str = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(RiderFeedback)
    if rider_id:
        query = query.where(RiderFeedback.rider_id == rider_id)
    
    query = query.order_by(RiderFeedback.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/road-conditions", response_model=RoadConditionResponse)
async def update_road_condition(
    condition: RoadConditionCreate,
    db: AsyncSession = Depends(get_db)
):
    db_condition = RoadConditionUpdate(**condition.model_dump())
    db.add(db_condition)
    
    result = await db.execute(select(Road).where(Road.id == condition.road_id))
    road = result.scalar_one_or_none()
    
    if road:
        road.road_status = condition.new_status
    
    await db.commit()
    await db.refresh(db_condition)
    
    return db_condition


@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(db: AsyncSession = Depends(get_db)):
    total_feedback = await db.scalar(select(func.count(RiderFeedback.id)))
    
    if total_feedback and total_feedback > 0:
        result = await db.execute(select(RiderFeedback))
        feedbacks = result.scalars().all()
        
        ai_avg = sum(f.estimated_time_minutes or 0 for f in feedbacks) / total_feedback
        actual_avg = sum(f.actual_time_minutes for f in feedbacks) / total_feedback
        
        overridden = sum(1 for f in feedbacks if f.ai_route_path != f.actual_route_path)
        cost_savings = (actual_avg - ai_avg) * 0.5 * overridden
    else:
        ai_avg = 0
        actual_avg = 0
        overridden = 0
        cost_savings = 0
    
    active_riders = await db.scalar(
        select(func.count(Rider.id)).where(Rider.is_active == True)
    ) or 0
    
    blocked_roads = await db.scalar(
        select(func.count(Road.id)).where(Road.road_status == "blocked")
    ) or 0
    
    return AnalyticsSummary(
        total_deliveries=total_feedback or 0,
        ai_avg_time=round(ai_avg, 2),
        actual_avg_time=round(actual_avg, 2),
        routes_overridden=overridden,
        cost_savings=round(cost_savings, 2),
        active_riders=active_riders,
        blocked_roads=blocked_roads
    )


@router.get("/analytics/problematic-roads", response_model=List[ProblematicRoadResponse])
async def get_problematic_roads(db: AsyncSession = Depends(get_db)):
    engine = LearningEngine(db)
    return await engine.get_problematic_roads()


@router.get("/learned-shortcuts")
async def get_learned_shortcuts(db: AsyncSession = Depends(get_db)):
    engine = LearningEngine(db)
    return await engine.get_learned_shortcuts()


@router.post("/auth/register", response_model=RiderResponse)
async def register_rider(rider: RiderCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Rider).where(Rider.rider_id == rider.rider_id)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Rider ID already exists")
    
    db_rider = Rider(
        rider_id=rider.rider_id,
        name=rider.name,
        phone=rider.phone,
        trust_score=1.0
    )
    db.add(db_rider)
    await db.commit()
    await db.refresh(db_rider)
    
    return db_rider


@router.post("/auth/login", response_model=TokenResponse)
async def login_rider(rider_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Rider).where(Rider.rider_id == rider_id, Rider.is_active == True)
    )
    rider = result.scalar_one_or_none()
    
    if not rider:
        raise HTTPException(status_code=404, detail="Rider not found")
    
    access_token = create_access_token(data={"sub": rider.rider_id})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.websocket("/ws/rider/{rider_id}")
async def rider_websocket_endpoint(websocket: WebSocket, rider_id: str):
    await handle_rider_websocket(websocket, rider_id)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket):
    await handle_admin_websocket(websocket)
