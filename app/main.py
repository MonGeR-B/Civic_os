from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import tickets

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Unified Enterprise Core for Urban Modernization & Resource Routing",
    version="1.0.0"
)

# Enable CORS so your frontend mockups can send requests easily without blocking
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register our spatial ticket processing router
app.include_router(tickets.router, prefix=settings.API_V1_STR)

@app.get("/")
async def root_check():
    return {
        "system_status": "ONLINE",
        "region": "West Bengal",
        "framework": "FastAPI Async Core"
    }