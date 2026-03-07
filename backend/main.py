from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
import os
from backend.services.auth_service import ensure_users_db, authenticate_user, get_user_by_id, sanitize_user
from backend.services.access_control import (
    get_default_classification_for_role,
    get_assignable_classifications_for_role,
)
from backend.services.auto_report_service import start_scheduler, stop_scheduler, get_reports_for_user
from backend.models.schemas import Role

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
ensure_users_db()

# Import routers
from backend.routers import reports

app.include_router(reports.router, prefix="/api", tags=["reports"])


@app.on_event("startup")
async def on_startup():
    # Run report generation every hour; each user is generated only when due.
    start_scheduler(interval_seconds=3600)


@app.on_event("shutdown")
async def on_shutdown():
    stop_scheduler()


def _get_current_user_from_cookie(request: Request):
    user_id = request.cookies.get("auth_user_id")
    if not user_id:
        return None
    user = get_user_by_id(user_id)
    if not user or not user.get("is_active", True):
        return None
    return sanitize_user(user)


def _require_user_or_redirect(request: Request):
    user = _get_current_user_from_cookie(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return user


@app.get("/login")
async def login_page(request: Request):
    """Render login page."""
    current_user = _get_current_user_from_cookie(request)
    if current_user:
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login_submit(request: Request, email: str = Form(...), password: str = Form(...)):
    """Handle login form submission."""
    user = authenticate_user(email, password)
    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid credentials. Try one of the demo users."},
            status_code=401,
        )

    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="auth_user_id",
        value=user["user_id"],
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 8,
    )
    return response


@app.get("/logout")
async def logout():
    """Clear auth cookie and redirect to login."""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("auth_user_id")
    return response


@app.get("/api/auth/me")
async def auth_me(request: Request):
    """Return logged-in user profile for frontend bootstrapping."""
    user = _get_current_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user_role = Role(user["role"])
    default_classification = get_default_classification_for_role(user_role).value
    return {
        "user": user,
        "default_classification": default_classification,
    }

# Root endpoint
@app.get("/")
async def home(request: Request):
    """Main dashboard"""
    auth_or_redirect = _require_user_or_redirect(request)
    if isinstance(auth_or_redirect, RedirectResponse):
        return auth_or_redirect

    user = auth_or_redirect
    default_classification = get_default_classification_for_role(Role(user["role"])).value
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "default_classification": default_classification,
        },
    )

@app.get("/upload")
async def upload_manager(request: Request):
    """Upload manager page for document uploads (Finance/Management/Admin only)"""
    auth_or_redirect = _require_user_or_redirect(request)
    if isinstance(auth_or_redirect, RedirectResponse):
        return auth_or_redirect

    user = auth_or_redirect
    user_role = Role(user["role"])
    
    # Restrict upload access to Finance, Management, and Admin only
    if user_role not in [Role.FINANCE, Role.MANAGEMENT, Role.ADMIN]:
        return templates.TemplateResponse(
            "access_denied.html",
            {
                "request": request,
                "user": user,
                "message": "Upload access is restricted to Finance, Management, and Admin users only."
            },
            status_code=403
        )
    
    default_classification = get_default_classification_for_role(user_role).value
    allowed_classifications = [
        classification.value for classification in get_assignable_classifications_for_role(user_role)
    ]
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "user": user,
            "default_classification": default_classification,
            "allowed_classifications": allowed_classifications,
        },
    )


@app.get("/auto-reports")
async def auto_reports_page(request: Request):
    """View scheduled auto-generated reports for the current user."""
    auth_or_redirect = _require_user_or_redirect(request)
    if isinstance(auth_or_redirect, RedirectResponse):
        return auth_or_redirect

    user = auth_or_redirect
    reports = get_reports_for_user(user)
    frequency_days = int(user.get("report_frequency_days", 7) or 7)

    return templates.TemplateResponse(
        "auto_reports.html",
        {
            "request": request,
            "user": user,
            "reports": reports,
            "frequency_days": frequency_days,
        },
    )

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
