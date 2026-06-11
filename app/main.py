from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import tickets, trees

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
app.include_router(trees.router, prefix=settings.API_V1_STR)

# Serve uploaded files (verification photos) over HTTP
from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

from fastapi.responses import HTMLResponse
import os

@app.get("/", response_class=HTMLResponse)
async def root_dashboard():
    # Load and serve the Visual Control Room dashboard directly at the root URL
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dashboard_path = os.path.join(base_dir, "dashboard.html")
    if os.path.exists(dashboard_path):
        with open(dashboard_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content)
    return HTMLResponse(content="<h1>Dashboard file not found.</h1>", status_code=404)