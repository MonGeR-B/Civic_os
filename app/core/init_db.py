import asyncio
from app.core.database import engine, Base
from app.models.models import User, Ticket, TreeTracker

async def init_models():
    async with engine.begin() as conn:
        # Drop all tables and recreate them cleanly (perfect for rapid prototyping)
        print("Dropping old tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating new spatial tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database initialization complete. PostGIS tables are ready!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_models())