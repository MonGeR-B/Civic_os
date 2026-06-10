import os
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.models import TreeTracker

router = APIRouter(prefix="/trees", tags=["Green Canopy"])

# Create a specialized directory for tree assets
TREE_UPLOAD_DIR = os.path.join("uploads", "trees")
os.makedirs(TREE_UPLOAD_DIR, exist_ok=True)

@router.post("/plant")
async def log_planted_tree(
    species: str = Form(...),          # e.g., 'Krishnachura', 'Neem'
    latitude: float = Form(...),
    longitude: float = Form(...),
    planted_by: int = Form(...),       # Worker User ID
    file: UploadFile = File(...),      # Verification photo of the sapling
    db: AsyncSession = Depends(get_db)
):
    # 1. Save the tree photo locally
    file_path = os.path.join(TREE_UPLOAD_DIR, f"{species}_{planted_by}_{file.filename}")
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    # 2. Build spatial point format for PostGIS
    spatial_point = f"POINT({longitude} {latitude})"

    # 3. Write record to database
    new_tree = TreeTracker(
        species=species,
        image_url=file_path,
        location=spatial_point,
        planted_by=planted_by
    )
    
    db.add(new_tree)
    await db.commit()
    
    return {
        "status": "success",
        "message": f"New {species} tree logged into city canopy tracking registry."
    }

@router.get("/map")
async def get_canopy_map(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all trees from the PostGIS database.
    We use func.ST_X and func.ST_Y to extract the raw spatial coordinates 
    directly out of the geometry column into basic numbers the frontend can read.
    """
    query = select(
        TreeTracker.id,
        TreeTracker.species,
        TreeTracker.image_url,
        func.ST_Y(TreeTracker.location).label("latitude"),
        func.ST_X(TreeTracker.location).label("longitude"),
        TreeTracker.planted_at
    )
    
    result = await db.execute(query)
    trees = result.all()
    
    # Format database rows cleanly into a standard list of dictionary objects
    map_features = []
    for tree in trees:
        map_features.append({
            "id": tree.id,
            "species": tree.species,
            "image_url": tree.image_url,
            "coordinates": {
                "lat": tree.latitude,
                "lng": tree.longitude
            },
            "planted_at": tree.planted_at
        })
        
    return {
        "total_trees_logged": len(map_features),
        "features": map_features
    }