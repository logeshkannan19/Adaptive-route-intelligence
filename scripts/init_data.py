import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.database.database import SessionLocal, Base, engine
from backend.models.models import Location, Road, Route, RiderFeedback


Base.metadata.create_all(bind=engine)


ERBIL_LOCATIONS = [
    {"name": "City Center", "latitude": 36.1911, "longitude": 43.9939, "location_type": "district"},
    {"name": "Airport Road", "latitude": 36.2056, "longitude": 43.9633, "location_type": "highway"},
    {"name": "Ankara Street", "latitude": 36.1989, "longitude": 43.9722, "location_type": "street"},
    {"name": "60M Street", "latitude": 36.1844, "longitude": 43.9811, "location_type": "street"},
    {"name": "Kurdistan Parliament", "latitude": 36.1722, "longitude": 43.9778, "location_type": "landmark"},
    {"name": "Family Mall", "latitude": 36.2100, "longitude": 43.9556, "location_type": "mall"},
    {"name": "Ainkawa", "latitude": 36.1689, "longitude": 43.9911, "location_type": "district"},
    {"name": "Kalis", "latitude": 36.1567, "longitude": 43.9856, "location_type": "district"},
    {"name": "Bazyan", "latitude": 36.1478, "longitude": 43.9756, "location_type": "district"},
    {"name": "MamOST", "latitude": 36.1622, "longitude": 43.9656, "location_type": "district"},
    {"name": "Shoresh", "latitude": 36.1756, "longitude": 43.9522, "location_type": "district"},
    {"name": "Industrial Zone", "latitude": 36.2156, "longitude": 43.9456, "location_type": "industrial"},
    {"name": "Hawler Medical", "latitude": 36.1889, "longitude": 43.9667, "location_type": "hospital"},
    {"name": "French Village", "latitude": 36.1956, "longitude": 43.9556, "location_type": "residential"},
    {"name": "Dream City", "latitude": 36.2022, "longitude": 43.9489, "location_type": "residential"},
    {"name": "Baghdad Road Junction", "latitude": 36.2200, "longitude": 43.9256, "location_type": "junction"},
    {"name": "Kurdistan University", "latitude": 36.1456, "longitude": 43.9656, "location_type": "university"},
    {"name": "Sports City", "latitude": 36.1778, "longitude": 43.9489, "location_type": "stadium"},
    {"name": "Erbil Castle", "latitude": 36.1911, "longitude": 43.9778, "location_type": "landmark"},
    {"name": "Central Market", "latitude": 36.1933, "longitude": 43.9856, "location_type": "market"},
]

ERBIL_ROADS = [
    {"source": "City Center", "target": "Ankara Street", "distance": 1.2, "status": "open"},
    {"source": "City Center", "target": "60M Street", "distance": 0.8, "status": "open"},
    {"source": "City Center", "target": "Erbil Castle", "distance": 0.5, "status": "open"},
    {"source": "City Center", "target": "Central Market", "distance": 0.4, "status": "open"},
    {"source": "Ankara Street", "target": "Family Mall", "distance": 1.5, "status": "open"},
    {"source": "Ankara Street", "target": "French Village", "distance": 1.0, "status": "open"},
    {"source": "Ankara Street", "target": "Hawler Medical", "distance": 0.6, "status": "risky"},
    {"source": "60M Street", "target": "Kurdistan Parliament", "distance": 1.1, "status": "open"},
    {"source": "60M Street", "target": "Ainkawa", "distance": 1.3, "status": "open"},
    {"source": "60M Street", "target": "Shoresh", "distance": 1.8, "status": "open"},
    {"source": "Airport Road", "target": "Family Mall", "distance": 2.0, "status": "open"},
    {"source": "Airport Road", "target": "Dream City", "distance": 1.6, "status": "open"},
    {"source": "Airport Road", "target": "Industrial Zone", "distance": 2.5, "status": "open"},
    {"source": "Family Mall", "target": "French Village", "distance": 0.9, "status": "open"},
    {"source": "Family Mall", "target": "Dream City", "distance": 1.2, "status": "open"},
    {"source": "Ainkawa", "target": "Kalis", "distance": 1.4, "status": "open"},
    {"source": "Kalis", "target": "Bazyan", "distance": 1.1, "status": "open"},
    {"source": "Bazyan", "target": "MamOST", "distance": 1.5, "status": "risky"},
    {"source": "MamOST", "target": "Kurdistan University", "distance": 1.3, "status": "open"},
    {"source": "MamOST", "target": "Shoresh", "distance": 1.6, "status": "flooded"},
    {"source": "Shoresh", "target": "Sports City", "distance": 0.8, "status": "open"},
    {"source": "Sports City", "target": "Dream City", "distance": 1.4, "status": "open"},
    {"source": "Industrial Zone", "target": "Baghdad Road Junction", "distance": 3.0, "status": "open"},
    {"source": "Baghdad Road Junction", "target": "Dream City", "distance": 1.8, "status": "blocked"},
    {"source": "Kurdistan Parliament", "target": "Ainkawa", "distance": 1.5, "status": "open"},
    {"source": "Kurdistan University", "target": "Bazyan", "distance": 1.0, "status": "open"},
    {"source": "French Village", "target": "Shoresh", "distance": 1.3, "status": "risky"},
    {"source": "French Village", "target": "Dream City", "distance": 0.9, "status": "open"},
    {"source": "Erbil Castle", "target": "Central Market", "distance": 0.3, "status": "open"},
    {"source": "Central Market", "target": "Ainkawa", "distance": 1.2, "status": "open"},
]


def init_database():
    db = SessionLocal()
    
    try:
        existing = db.query(Location).first()
        if existing:
            print("Database already initialized")
            return
        
        location_map = {}
        for loc_data in ERBIL_LOCATIONS:
            loc = Location(**loc_data)
            db.add(loc)
            db.flush()
            location_map[loc_data["name"]] = loc.id
        
        for road_data in ERBIL_ROADS:
            source_id = location_map.get(road_data["source"])
            target_id = location_map.get(road_data["target"])
            
            if source_id and target_id:
                road = Road(
                    source_id=source_id,
                    target_id=target_id,
                    distance_km=road_data["distance"],
                    road_status=road_data["status"],
                    is_flood_prone=road_data["status"] == "flooded",
                    base_weight=1.0,
                    current_weight=1.0
                )
                db.add(road)
        
        db.commit()
        print("Database initialized with Erbil city data")
        print(f"Created {len(location_map)} locations and {len(ERBIL_ROADS)} roads")
        
    except Exception as e:
        db.rollback()
        print(f"Error initializing database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
