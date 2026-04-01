import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from backend.database.database import Base, get_db
from backend.models.models import Location, Road, Rider, RiderFeedback
from backend.services.routing_engine import RoutingEngine, LearningEngine
from backend.main import app


TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def sample_locations(test_db):
    locations = [
        Location(name="City Center", latitude=36.1911, longitude=43.9939, location_type="district"),
        Location(name="Airport Road", latitude=36.2056, longitude=43.9633, location_type="highway"),
        Location(name="Ankara Street", latitude=36.1989, longitude=43.9722, location_type="street"),
        Location(name="Family Mall", latitude=36.2100, longitude=43.9556, location_type="mall"),
    ]
    
    for loc in locations:
        test_db.add(loc)
    
    await test_db.commit()
    
    for loc in locations:
        await test_db.refresh(loc)
    
    return locations


@pytest.fixture
async def sample_roads(test_db, sample_locations):
    roads = [
        Road(
            source_id=sample_locations[0].id,
            target_id=sample_locations[1].id,
            distance_km=2.5,
            road_status="open"
        ),
        Road(
            source_id=sample_locations[0].id,
            target_id=sample_locations[2].id,
            distance_km=1.2,
            road_status="open"
        ),
        Road(
            source_id=sample_locations[2].id,
            target_id=sample_locations[3].id,
            distance_km=1.5,
            road_status="risky"
        ),
    ]
    
    for road in roads:
        test_db.add(road)
    
    await test_db.commit()
    
    return roads


@pytest.mark.asyncio
async def test_routing_engine_build_graph(test_db, sample_locations, sample_roads):
    engine = RoutingEngine(test_db)
    await engine.build_graph()
    
    assert len(engine.graph.nodes) == 4
    assert len(engine.graph.edges) >= 2


@pytest.mark.asyncio
async def test_dijkstra_route(test_db, sample_locations, sample_roads):
    engine = RoutingEngine(test_db)
    await engine.build_graph()
    
    path = await engine.dijkstra_route(
        sample_locations[0].id,
        sample_locations[3].id
    )
    
    assert path is not None
    assert len(path) >= 2
    assert path[0] == sample_locations[0].id
    assert path[-1] == sample_locations[3].id


@pytest.mark.asyncio
async def test_route_details(test_db, sample_locations, sample_roads):
    engine = RoutingEngine(test_db)
    await engine.build_graph()
    
    path = await engine.dijkstra_route(
        sample_locations[0].id,
        sample_locations[3].id
    )
    
    details = await engine.get_route_details(path)
    
    assert "path" in details
    assert "total_distance_km" in details
    assert "estimated_time_minutes" in details
    assert details["total_distance_km"] > 0


@pytest.mark.asyncio
async def test_learning_engine_process_feedback(test_db, sample_locations, sample_roads):
    feedback = RiderFeedback(
        rider_id="RIDER_001",
        ai_route_path=[sample_locations[0].id, sample_locations[1].id],
        actual_route_path=[sample_locations[0].id, sample_locations[2].id, sample_locations[1].id],
        actual_time_minutes=30.0,
        delay_minutes=5.0,
        shortcut_used=True
    )
    
    test_db.add(feedback)
    await test_db.flush()
    
    learning_engine = LearningEngine(test_db)
    await learning_engine.process_feedback(feedback)
    
    await test_db.commit()
    
    assert feedback.id is not None


@pytest.mark.asyncio
async def test_get_neighbors(test_db, sample_locations, sample_roads):
    engine = RoutingEngine(test_db)
    await engine.build_graph()
    
    neighbors = await engine.get_neighbors(sample_locations[0].id)
    
    assert len(neighbors) >= 2
    assert all("node_id" in n for n in neighbors)


@pytest.mark.asyncio
async def test_learned_shortcuts(test_db, sample_locations, sample_roads):
    learning_engine = LearningEngine(test_db)
    shortcuts = await learning_engine.get_learned_shortcuts()
    
    assert isinstance(shortcuts, list)
