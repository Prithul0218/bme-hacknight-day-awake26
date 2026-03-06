from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="FinanceBuddy",
    description="AI-powered financial document translator for departments",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files and templates
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Import routers
from backend.routers import reports

app.include_router(reports.router, prefix="/api", tags=["reports"])

# Root endpoint
@app.get("/")
async def home(request: Request):
    """Main dashboard"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/upload")
async def upload_manager(request: Request):
    """Upload manager page for document uploads"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": os.getenv("APP_NAME", "FinanceBuddy"),
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY"))
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
