import enum
from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.core.database import Base

# Enums for strict status tracking
class UserRole(str, enum.Enum):
    citizen = "citizen"
    field_staff = "field_staff"
    ward_admin = "ward_admin"

class TicketStatus(str, enum.Enum):
    open = "open"
    assigned = "assigned"
    resolved = "resolved"

# 1. Users Table
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.citizen)
    ward_id = Column(Integer, nullable=True)  # Links field staff to specific wards

# 2. Unified Tickets Table (Garbage & Streetlights)
class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)  # 'garbage' or 'streetlight'
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.open)
    image_url_before = Column(String, nullable=False)
    image_url_after = Column(String, nullable=True)
    
    # This is the PostGIS magic line. SRID 4326 is the standard GPS coordinate system.
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    reporter_id = Column(Integer, ForeignKey("users.id"))
    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# 3. Green Canopy Tracker Table
class TreeTracker(Base):
    __tablename__ = "tree_tracker"
    id = Column(Integer, primary_key=True, index=True)
    species = Column(String, nullable=False)
    image_url = Column(String, nullable=False)
    
    location = Column(Geometry(geometry_type='POINT', srid=4326), nullable=False)
    
    planted_by = Column(Integer, ForeignKey("users.id"))
    planted_at = Column(DateTime(timezone=True), server_default=func.now())