import asyncio
import random
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.models import Ticket, TreeTracker, TicketStatus

# Spatial bounding box coordinates for Greater Kolkata area
KOLKATA_BOUNDS = {
    "lat_min": 22.5000,  # Around South Kolkata / Gariahat
    "lat_max": 22.6000,  # Around North Kolkata / Salt Lake / New Town
    "lng_min": 88.3300,  # Near Hooghly River / Central Business District
    "lng_max": 88.4500   # Deep Sector V / New Town Action Area
}

CATEGORIES = ["garbage", "streetlight"]
TREE_SPECIES = ["Krishnachura", "Radhachura", "Neem", "Devdaru", "Banyan"]

def generate_random_kolkata_gps():
    lat = random.uniform(KOLKATA_BOUNDS["lat_min"], KOLKATA_BOUNDS["lat_max"])
    lng = random.uniform(KOLKATA_BOUNDS["lng_min"], KOLKATA_BOUNDS["lng_max"])
    return lat, lng

async def seed_bulk_demo_data():
    async with SessionLocal() as db:
        print("Generating 60 active civic issues across Kolkata...")
        for i in range(60):
            lat, lng = generate_random_kolkata_gps()
            category = random.choice(CATEGORIES)
            
            # Mix up statuses to show historical data on the dashboard
            status = random.choice([TicketStatus.open, TicketStatus.assigned, TicketStatus.resolved])
            assigned_to = 2 if status in [TicketStatus.assigned, TicketStatus.resolved] else None
            image_after = "uploads/mock_resolved.jpg" if status == TicketStatus.resolved else None

            ticket = Ticket(
                category=category,
                status=status,
                image_url_before=f"uploads/mock_{category}_issue.jpg",
                image_url_after=image_after,
                location=f"POINT({lng} {lat})",
                reporter_id=1,
                assigned_to=assigned_to,
                created_at=datetime.utcnow() - timedelta(days=random.randint(0, 5))
            )
            db.add(ticket)

        print("Generating 80 urban forestry canopy entries across Kolkata...")
        for j in range(80):
            lat, lng = generate_random_kolkata_gps()
            species = random.choice(TREE_SPECIES)

            tree = TreeTracker(
                species=species,
                image_url="uploads/trees/mock_sapling.jpg",
                location=f"POINT({lng} {lat})",
                planted_by=2,
                planted_at=datetime.utcnow() - timedelta(days=random.randint(0, 30))
            )
            db.add(tree)

        await db.commit()
        print("\n=== SUCCESS ===")
        print("Successfully injected 140 live spatial points into Greater Kolkata coordinates!")

if __name__ == "__main__":
    asyncio.run(seed_bulk_demo_data())