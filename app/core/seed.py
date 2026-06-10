import asyncio
from app.core.database import SessionLocal
from app.models.models import User, UserRole

async def seed_data():
    async with SessionLocal() as db:
        # Create a citizen to report the issue
        citizen = User(name="Kolkata Citizen", role=UserRole.citizen)
        # Create a worker assigned to Ward 1
        worker = User(name="Ward 1 Sanitation Officer", role=UserRole.field_staff, ward_id=1)
        
        db.add_all([citizen, worker])
        await db.commit()
        print("Mock users seeded perfectly. User ID 1 is your Citizen.")

if __name__ == "__main__":
    asyncio.run(seed_data())