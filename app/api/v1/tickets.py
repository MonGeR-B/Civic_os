import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.elements import WKTElement
from app.core.database import get_db
from app.models.models import Ticket, TicketStatus

router = APIRouter(prefix="/tickets", tags=["Tickets"])

# Directory to store incoming verification photos locally for the prototype
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/report")
async def report_issue(
    category: str = Form(...),          # 'garbage' or 'streetlight'
    latitude: float = Form(...),        # e.g., 22.5726
    longitude: float = Form(...),       # e.g., 88.3639
    reporter_id: int = Form(...),       # Mock citizen user ID
    file: UploadFile = File(...),       # The live verification photo
    db: AsyncSession = Depends(get_db)
):
    # Normalize category input to lowercase to prevent validation issues
    category = category.strip().lower()
    if category not in ["garbage", "streetlight"]:
        raise HTTPException(status_code=400, detail="Invalid civic category.")

    # 1. Save the file to our local mock-S3 uploads folder
    file_path = os.path.join(UPLOAD_DIR, f"{category}_{reporter_id}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 2. Format coordinates into a Well-Known Text (WKT) string for PostGIS
    # WARNING: PostGIS expects spatial coordinates in LONGITUDE, LATITUDE order.
    spatial_point = f"POINT({longitude} {latitude})"

    # 3. Instantiate the new spatial Ticket record
    new_ticket = Ticket(
        category=category,
        status=TicketStatus.open,
        image_url_before=file_path,
        location=spatial_point,  # GeoAlchemy2 implicitly converts standard WKT text strings here
        reporter_id=reporter_id,
        assigned_to=None         # Initially unassigned; handled by allocation engine next
    )

    db.add(new_ticket)
    await db.flush()  # Forces generation of the Ticket ID without ending transaction
    
    return {
        "status": "success",
        "message": f"Civic {category} ticket registered successfully.",
        "ticket_id": new_ticket.id,
        "coordinates": {"lat": latitude, "lng": longitude}
    }