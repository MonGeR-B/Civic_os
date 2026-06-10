from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Create the async engine for PostGIS
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,  # Set to True if you want to see raw SQL logs in your terminal
    future=True
)

# Create a session maker for handling transactions
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for our SQLAlchemy Models
class Base(DeclarativeBase):
    pass

# Dependency to inject DB sessions into FastAPI routes cleanly
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()