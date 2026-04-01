from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    location_type: str = Field(default="point")
    city: str = "Erbil"


class LocationCreate(LocationBase):
    pass


class LocationResponse(LocationBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoadBase(BaseModel):
    source_id: int = Field(..., gt=0)
    target_id: int = Field(..., gt=0)
    distance_km: float = Field(..., gt=0)
    base_weight: float = 1.0
    road_status: str = "open"
    is_flood_prone: bool = False
    road_type: str = "primary"
    max_speed_kmh: int = 50
    
    @field_validator('source_id', 'target_id')
    def validate_different_nodes(cls, v, info):
        if 'source_id' in info.data and 'target_id' in info.data:
            if info.data['source_id'] == info.data['target_id']:
                raise ValueError('source_id and target_id must be different')
        return v


class RoadCreate(RoadBase):
    pass


class RoadUpdate(BaseModel):
    road_status: Optional[str] = None
    is_flood_prone: Optional[bool] = None
    blocked_after_hour: Optional[int] = Field(None, ge=0, le=23)
    current_weight: Optional[float] = Field(None, ge=0.1, le=5.0)
    max_speed_kmh: Optional[int] = Field(None, ge=1, le=200)


class RoadResponse(RoadBase):
    id: int
    current_weight: float
    avg_delay_minutes: float
    usage_count: int
    is_flood_prone: bool
    blocked_after_hour: Optional[int]
    
    class Config:
        from_attributes = True


class RouteRequest(BaseModel):
    start_location_id: int = Field(..., gt=0)
    end_location_id: int = Field(..., gt=0)
    algorithm: str = "dijkstra"
    use_mapbox: bool = False
    
    @field_validator('start_location_id', 'end_location_id')
    def validate_different_locations(cls, v, info):
        if 'start_location_id' in info.data and 'end_location_id' in info.data:
            if info.data['start_location_id'] == info.data['end_location_id']:
                raise ValueError('start and end locations must be different')
        return v


class RouteResponse(BaseModel):
    id: Optional[int] = None
    path: List[int]
    path_names: List[str]
    total_distance_km: float
    estimated_time_minutes: float
    total_weight: float
    edges: List[Dict[str, Any]]
    route_type: str = "ai_generated"
    algorithm_used: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MultiRouteResponse(BaseModel):
    routes: List[RouteResponse]
    alternatives: int


class FeedbackCreate(BaseModel):
    route_id: Optional[int] = None
    rider_id: str = Field(..., min_length=3, max_length=50)
    ai_route_path: List[int] = Field(..., min_length=2)
    actual_route_path: List[int] = Field(..., min_length=2)
    actual_time_minutes: float = Field(..., ge=0)
    estimated_time_minutes: float = 0
    delay_minutes: float = 0
    issues_reported: List[str] = []
    shortcut_used: bool = False
    rating: int = Field(default=5, ge=1, le=5)
    
    @field_validator('actual_time_minutes')
    def validate_time(cls, v):
        if v <= 0:
            raise ValueError('actual_time_minutes must be positive')
        return v


class FeedbackResponse(FeedbackCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class RoadConditionCreate(BaseModel):
    road_id: int
    new_status: str
    reported_by: str
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class RoadConditionResponse(BaseModel):
    id: int
    road_id: int
    new_status: str
    reported_by: str
    notes: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    is_verified: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AnalyticsSummary(BaseModel):
    total_deliveries: int
    ai_avg_time: float
    actual_avg_time: float
    routes_overridden: int
    cost_savings: float
    active_riders: int
    blocked_roads: int


class ProblematicRoadResponse(BaseModel):
    road_id: int
    issue_count: int
    avg_delay: float
    status: str
    weight_increase: float


class RiderCreate(BaseModel):
    rider_id: str = Field(..., min_length=3, max_length=50)
    name: str
    phone: Optional[str] = None


class RiderResponse(BaseModel):
    id: int
    rider_id: str
    name: Optional[str]
    phone: Optional[str]
    trust_score: float
    total_deliveries: int
    is_active: bool
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    cache: str
    timestamp: datetime
