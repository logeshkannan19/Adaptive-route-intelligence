import sys
import os
import random
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from backend.database.database import SessionLocal
from backend.models.models import Location, Road, RiderFeedback
from backend.services.routing_engine import RoutingEngine, LearningEngine


def simulate_rider_feedback(num_riders=5, deliveries_per_rider=3):
    db = SessionLocal()
    
    locations = db.query(Location).all()
    if not locations:
        print("No locations in database. Run init_data.py first.")
        return
    
    location_ids = [loc.id for loc in locations]
    rider_ids = [f"RIDER_{i:03d}" for i in range(1, num_riders + 1)]
    
    print(f"\n=== Simulating {num_riders} riders with {deliveries_per_rider} deliveries each ===\n")
    
    for rider_id in rider_ids:
        for delivery in range(deliveries_per_rider):
            start_id = random.choice(location_ids)
            end_id = random.choice([lid for lid in location_ids if lid != start_id])
            
            engine = RoutingEngine(db)
            ai_path = engine.dijkstra_route(start_id, end_id)
            
            if not ai_path:
                continue
            
            details = engine.get_route_details(ai_path)
            
            actual_path = ai_path.copy()
            
            if random.random() < 0.6:
                mid = random.randint(1, len(actual_path) - 2) if len(actual_path) > 2 else 1
                detour = random.choice([lid for lid in location_ids if lid != actual_path[mid]])
                actual_path.insert(mid, detour)
            
            shortcut_used = len(actual_path) < len(ai_path) or (random.random() < 0.3 and len(actual_path) == len(ai_path))
            
            time_multiplier = 1.0 + (random.random() * 0.5)
            actual_time = details["estimated_time_minutes"] * time_multiplier
            
            delay = max(0, actual_time - details["estimated_time_minutes"])
            
            issues = []
            if delay > 5:
                issues.append("traffic_delay")
            if random.random() < 0.2:
                issues.append(f"road_{random.randint(1, 10)}:checkpoint")
            if random.random() < 0.1:
                issues.append("road_blocked")
            
            deviation = len(actual_path) - len(ai_path)
            shortcut_used = deviation < 0 or (random.random() < 0.3 and deviation == 0)
            
            feedback = RiderFeedback(
                rider_id=rider_id,
                ai_route_path=ai_path,
                actual_route_path=actual_path,
                actual_time_minutes=actual_time,
                delay_minutes=delay,
                issues_reported=issues,
                shortcut_used=shortcut_used
            )
            db.add(feedback)
            db.flush()
            
            learning_engine = LearningEngine(db)
            learning_engine.process_feedback(feedback)
            
            print(f"  {rider_id}: Delivery {delivery + 1}")
            print(f"    AI Path: {len(ai_path)} nodes, Est: {details['estimated_time_minutes']:.1f} min")
            print(f"    Actual:  {len(actual_path)} nodes, Actual: {actual_time:.1f} min, Delay: {delay:.1f} min")
            print(f"    Issues: {len(issues)}, Shortcut: {shortcut_used}")
            print()
            
            time.sleep(0.1)
    
    db.close()
    print("=== Simulation Complete ===\n")


def show_learning_results():
    db = SessionLocal()
    
    print("\n=== Learning Results ===\n")
    
    roads = db.query(Road).filter(Road.current_weight != Road.base_weight).all()
    
    if roads:
        print("Roads with adjusted weights:")
        for road in roads:
            change = ((road.current_weight - road.base_weight) / road.base_weight) * 100
            print(f"  Road {road.id}: weight {road.base_weight:.2f} -> {road.current_weight:.2f} ({change:+.1f}%)")
    else:
        print("No weight adjustments yet")
    
    engine = LearningEngine(db)
    shortcuts = engine.get_learned_shortcuts()
    
    if shortcuts:
        print("\nLearned shortcuts:")
        for sc in shortcuts:
            print(f"  {sc}")
    else:
        print("\nNo shortcuts learned yet")
    
    db.close()


if __name__ == "__main__":
    simulate_rider_feedback(num_riders=5, deliveries_per_rider=3)
    show_learning_results()
