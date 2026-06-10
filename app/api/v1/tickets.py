import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import Ticket, TicketStatus
from app.services.allocation import auto_allocate_ticket  # Import the engine
from sqlalchemy import select, func

router = APIRouter(prefix="/tickets", tags=["Tickets"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/report")
async def report_issue(
    category: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    reporter_id: int = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    if category not in ["garbage", "streetlight"]:
        raise HTTPException(status_code=400, detail="Invalid civic category.")

    # Save file locally
    file_path = os.path.join(UPLOAD_DIR, f"{category}_{reporter_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Build spatial point format for PostGIS
    spatial_point = f"POINT({longitude} {latitude})"

    # Instantiate base ticket
    new_ticket = Ticket(
        category=category,
        status=TicketStatus.open,
        image_url_before=file_path,
        location=spatial_point,
        reporter_id=reporter_id,
        assigned_to=None
    )

    db.add(new_ticket)
    
    # Run the automated allocation sequence
    assigned_officer = await auto_allocate_ticket(new_ticket, db)
    
    # Save everything securely to database
    await db.commit()
    await db.refresh(new_ticket)
    
    # Build a descriptive assignment message for the demonstration
    assignment_log = (
        f"Auto-routed to Officer (ID: {assigned_officer.id})" 
        if assigned_officer 
        else "Queued as Pending (All field staff overloaded)"
    )
    
    return {
        "status": "success",
        "ticket_id": new_ticket.id,
        "category": new_ticket.category,
        "ticket_status": new_ticket.status,
        "allocation_result": assignment_log,
        "coordinates": {"lat": latitude, "lng": longitude}
    }

@router.get("/map")
async def get_tickets_map(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all active and resolved tickets with raw latitudes and longitudes
    extracted straight out of the PostGIS geometry field.
    """
    query = select(
        Ticket.id,
        Ticket.category,
        Ticket.status,
        Ticket.image_url_before,
        func.ST_Y(Ticket.location).label("latitude"),
        func.ST_X(Ticket.location).label("longitude"),
        Ticket.created_at
    )
    
    result = await db.execute(query)
    tickets = result.all()
    
    ticket_features = []
    for t in tickets:
        ticket_features.append({
            "id": t.id,
            "category": t.category,
            "status": t.status,
            "image_url": t.image_url_before,
            "coordinates": {
                "lat": t.latitude,
                "lng": t.longitude
            },
            "created_at": t.created_at
        })
        
    return {"total_tickets": len(ticket_features), "features": ticket_features}