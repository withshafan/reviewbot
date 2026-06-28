"""
Web routes for ReviewBot HTML pages and the reviews API.
Serves the unified single-page dashboard and API endpoints.
"""

import os
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, text

from app.database import SessionLocal
from app.models import ReviewHistory

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ── Unified Dashboard Route ──
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """Render the single-page dashboard with all required context."""
    # 1. Fetch Overview Stats
    total_reviews = 0
    total_issues = 0
    total_repos = 0
    
    # 2. Fetch Health Data
    db_ok = False
    last_review = None
    
    try:
        db = SessionLocal()
        # Overview Stats
        total_reviews = db.query(func.count(ReviewHistory.id)).scalar() or 0
        total_issues = db.query(func.coalesce(func.sum(ReviewHistory.total_issues), 0)).scalar()
        total_repos = db.query(
            func.count(func.distinct(ReviewHistory.owner + '/' + ReviewHistory.repo))
        ).scalar() or 0
        
        # Health Check (DB)
        db.execute(text("SELECT 1"))
        db_ok = True
        last_review = db.query(ReviewHistory).order_by(ReviewHistory.created_at.desc()).first()
        db.close()
    except Exception as e:
        db_ok = False

    # Check environment variables for health
    gemini_ok = bool(os.getenv("GEMINI_API_KEY"))
    github_ok = bool(os.getenv("GITHUB_APP_ID")) and (
        os.path.exists("private_key.pem") or bool(os.getenv("GITHUB_PRIVATE_KEY"))
    )

    return templates.TemplateResponse(request, "dashboard.html", {
        # Overview stats
        "total_reviews": total_reviews,
        "total_issues": total_issues,
        "total_repos": total_repos,
        # Health checks
        "db_ok": db_ok,
        "gemini_ok": gemini_ok,
        "github_ok": github_ok,
        "last_review": last_review,
    })


# ── Redirects ──
@router.get("/docs", include_in_schema=False)
async def redirect_docs():
    """Redirect /docs to the API Docs tab of the dashboard."""
    return RedirectResponse(url="/?tab=api-docs")

@router.get("/redoc", include_in_schema=False)
async def redirect_redoc():
    """Redirect /redoc to the API Docs tab of the dashboard."""
    return RedirectResponse(url="/?tab=api-docs")


# ── Reviews API (JSON) ──
@router.get("/api/reviews", include_in_schema=False)
async def api_reviews():
    """Return review history as JSON for the dashboard charting and table."""
    try:
        db = SessionLocal()
        reviews = (
            db.query(ReviewHistory)
            .order_by(ReviewHistory.created_at.desc())
            .limit(100)
            .all()
        )
        result = [
            {
                "id": r.id,
                "owner": r.owner,
                "repo": r.repo,
                "pr_number": r.pr_number,
                "head_sha": r.head_sha,
                "total_issues": r.total_issues,
                "decision": r.decision,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in reviews
        ]
        db.close()
        return result
    except Exception:
        return []
