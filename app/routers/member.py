from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.models import User
from app.database.schemas import UserRole
from app.database.connection import get_db
from app.routers.auth import get_current_user
from app.utils.auth import login_required
from app.utils.dashboard import calculate_member_stats

router = APIRouter(prefix="/member", tags=["member"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
@login_required
async def member_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    
    # Calculate dashboard stats
    stats = calculate_member_stats(current_user["id"], db)
    dashboard_data = {
        "request": request,
        "stats": stats
    }

    return templates.TemplateResponse("member/dashboard.html", dashboard_data)

@router.get("/dashboard", response_class=HTMLResponse)
@login_required
async def member_dashboard(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    # Dummy data cho dashboard của member
    dashboard_data = {
        "request": request,
        "borrowed_books": [
            {
                "id": 1,
                "title": "Python Programming",
                "author": "John Smith",
                "borrow_date": "2024-02-01",
                "due_date": "2024-02-15",
                "status": "Active"
            },
            {
                "id": 2,
                "title": "Data Structures",
                "author": "Jane Doe",
                "borrow_date": "2024-01-20",
                "due_date": "2024-02-03",
                "status": "Overdue"
            }
        ],
        "favorite_books": [
            {
                "id": 1,
                "title": "Machine Learning Basics",
                "author": "Mike Wilson",
                "category": "Data Science",
                "available": True
            },
            {
                "id": 2,
                "title": "Web Development",
                "author": "Sarah Brown",
                "category": "Programming",
                "available": False
            },
            {
                "id": 3,
                "title": "Database Design",
                "author": "Tom Davis",
                "category": "Database",
                "available": True
            }
        ],
        "stats": {
            "total_borrowed": 2,
            "total_favorites": 3,
            "overdue_books": 1,
            "total_fee": 100
        }
    }
    
    return templates.TemplateResponse("member/dashboard.html", dashboard_data)

@router.get("/profile", response_class=HTMLResponse)
@login_required
async def member_profile(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/auth/login", status_code=303)
        
    db_user = db.query(User).filter(User.id == user["id"]).first()
    
    return templates.TemplateResponse(
        "auth/profile.html",
        {
            "request": request,
            "user": db_user,
            "has_face_id": db_user.face_embedding is not None
        }
    )