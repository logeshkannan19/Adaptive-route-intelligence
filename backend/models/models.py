from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, JSON, Index
from datetime import datetime
from database.database import Base


class Location(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_type = Column(String, default="point")
    city = Column(String, default="Erbil")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_location_coords', 'latitude', 'longitude'),
    )


class Road(Base):
    __tablename__ = "roads"
    
    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    target_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    base_weight = Column(Float, default=1.0)
    current_weight = Column(Float, default=1.0)
    road_status = Column(String, default="open", index=True)
    is_flood_prone = Column(Boolean, default=False)
    blocked_after_hour = Column(Integer, nullable=True)
    road_type = Column(String, default="primary")
    max_speed_kmh = Column(Integer, default=50)
    usage_count = Column(Integer, default=0)
    avg_delay_minutes = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_road_connection', 'source_id', 'target_id'),
        Index('idx_road_status', 'road_status'),
    )


class Route(Base):
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    start_location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    end_location_id = Column(Integer, ForeignKey("locations.id"), index=True)
    path_nodes = Column(JSON)
    total_distance = Column(Float)
    estimated_time_minutes = Column(Float)
    route_type = Column(String, default="ai_generated")
    algorithm_used = Column(String, default="dijkstra")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class Rider(Base):
    __tablename__ = "riders"
    
    id = Column(Integer, primary_key=True, index=True)
    rider_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    phone = Column(String)
    trust_score = Column(Float, default=1.0)
    total_deliveries = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class RiderFeedback(Base):
    __tablename__ = "rider_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True, index=True)
    rider_id = Column(String, nullable=False, index=True)
    ai_route_path = Column(JSON)
    actual_route_path = Column(JSON)
    actual_time_minutes = Column(Float)
    delay_minutes = Column(Float, default=0)
    issues_reported = Column(JSON, default=list)
    shortcut_used = Column(Boolean, default=False)
    rating = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_feedback_rider', 'rider_id', 'created_at'),
    )


class RoadConditionUpdate(Base):
    __tablename__ = "road_condition_updates"
    
    id = Column(Integer, primary_key=True, index=True)
    road_id = Column(Integer, ForeignKey("roads.id"), index=True)
    new_status = Column(String, nullable=False)
    reported_by = Column(String)
    notes = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=True)


class Analytics(Base):
    __tablename__ = "analytics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    hour = Column(Integer, default=0)
    ai_avg_time = Column(Float)
    actual_avg_time = Column(Float)
    total_deliveries = Column(Integer, default=0)
    routes_overridden = Column(Integer, default=0)
    cost_savings = Column(Float, default=0)
    road_issues_count = Column(Integer, default=0)
    
    __table_args__ = (
        Index('idx_analytics_date', 'date', 'hour'),
    )
