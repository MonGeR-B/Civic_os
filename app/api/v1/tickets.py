import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import Ticket, TicketStatus
from app.services.allocation import auto_allocate_ticket  # Import the engine
from sqlalchemy import select, func
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

router = APIRouter(prefix="/tickets", tags=["Tickets"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Spatial bounding box coordinates for Greater Kolkata area
KOLKATA_BOUNDS = {
    "lat_min": 22.5000,
    "lat_max": 22.6000,
    "lng_min": 88.3300,
    "lng_max": 88.4500
}

def get_ward_from_coordinates(lat: float, lng: float) -> int:
    lat_step = (KOLKATA_BOUNDS["lat_max"] - KOLKATA_BOUNDS["lat_min"]) / 4
    lng_step = (KOLKATA_BOUNDS["lng_max"] - KOLKATA_BOUNDS["lng_min"]) / 4
    
    row = int((lat - KOLKATA_BOUNDS["lat_min"]) / lat_step)
    col = int((lng - KOLKATA_BOUNDS["lng_min"]) / lng_step)
    
    row = max(0, min(3, row))
    col = max(0, min(3, col))
    
    return row * 4 + col + 1

def watermark_image(image_path: str, lat: float, lng: float):
    # Open the saved image
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    
    # Calculate ward and timestamp
    ward_id = get_ward_from_coordinates(lat, lng)
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    watermark_text = (
        f"CivicOS WB // WARD: {ward_id} // "
        f"LAT: {lat:.6f} LNG: {lng:.6f} // "
        f"TIME: {timestamp_str} // EVIDENCE SECURE"
    )
    
    width, height = img.size
    
    # Font size selection (approx 2.5% of height)
    font_size = max(16, int(height * 0.025))
    
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
        
    banner_height = font_size + 20
    draw.rectangle(
        [(0, height - banner_height), (width, height)],
        fill=(15, 23, 42)  # Dark slate background
    )
    
    # Draw text in light cyan (#22d3ee)
    text_color = (34, 211, 238)
    draw.text((15, height - banner_height + 8), watermark_text, fill=text_color, font=font)
    
    # Save the watermarked image
    img.save(image_path)

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

    # Build a clean filename and save locally
    safe_filename = f"{category}_{reporter_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # Apply Tamper-Proof Cryptographic Watermarking
    try:
        watermark_image(file_path, latitude, longitude)
    except Exception as e:
        print(f"Error applying watermark: {e}")

    # Store a URL-accessible path (served via /uploads static mount)
    image_url = f"/uploads/{safe_filename}"

    # Build spatial point format for PostGIS
    spatial_point = f"POINT({longitude} {latitude})"

    # Instantiate base ticket
    ward_id = get_ward_from_coordinates(latitude, longitude)
    new_ticket = Ticket(
        category=category,
        status=TicketStatus.open,
        image_url_before=image_url,
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
        "ward": ward_id,
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