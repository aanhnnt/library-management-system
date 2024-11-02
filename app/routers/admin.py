from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from ..database.schemas import UserRole
from ..routers.auth import get_current_user
from ..utils.auth import login_required
from sqlalchemy.orm import Session
from ..database.models import User
from ..database.connection import get_db

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
@login_required
async def admin_dashboard(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    # Dummy data matching your dashboard.html structure
    dashboard_data = {
        "request": request,
        "borrowed_books": 45,  # Total number of currently borrowed books
        "total_books": 150,    # Total books in library
        "total_rent_current_month": 2500,  # Total earnings this month
        "total_members": 75,   # Total number of members
        "recent_transactions": [
            (
                {"id": 1, "issue_date": "5", "rent_fee": 150},
                {"title": "Python Programming"}
            ),
            (
                {"id": 2, "issue_date": "10", "rent_fee": 200},
                {"title": "Data Structures"}
            ),
            (
                {"id": 3, "issue_date": "15", "rent_fee": 175},
                {"title": "Machine Learning Basics"}
            ),
            (
                {"id": 4, "issue_date": "20", "rent_fee": 225},
                {"title": "Web Development"}
            ),
            (
                {"id": 5, "issue_date": "25", "rent_fee": 190},
                {"title": "Database Design"}
            )
        ]
    }
    
    return templates.TemplateResponse("admin/dashboard.html", dashboard_data)

@router.get("/members", response_class=HTMLResponse)
@login_required
async def admin_view_members(request: Request, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    # Dummy member data
    members_data = {
        "request": request,
        "members": [
            {
                "id": 1,
                "name": "John Doe",
                "email": "john@example.com",
                "role": "Member",
                "status": "Active",
                "join_date": "2024-01-15",
                "books_borrowed": 3
            },
            {
                "id": 2,
                "name": "Jane Smith",
                "email": "jane@example.com",
                "role": "Member",
                "status": "Active",
                "join_date": "2024-02-01",
                "books_borrowed": 1
            },
            {
                "id": 3,
                "name": "Bob Wilson",
                "email": "bob@example.com",
                "role": "Member",
                "status": "Inactive",
                "join_date": "2024-01-20",
                "books_borrowed": 0
            }
        ],
        "total_members": 3,
        "active_members": 2,
        "inactive_members": 1
    }
    
    return templates.TemplateResponse("admin/members.html", members_data)

@router.get("/members/{member_id}", response_class=HTMLResponse)
@login_required
async def admin_view_member_detail(
    request: Request, 
    member_id: int, 
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    # Dummy data for a single member
    member_data = {
        "request": request,
        "member": {
            "id": member_id,
            "name": "John Doe",
            "email": "john@example.com",
            "role": "Member",
            "status": "Active",
            "join_date": "2024-01-15",
            "phone": "+1234567890",
            "address": "123 Main St, City, Country",
            "books_borrowed": 3
        },
        # Dummy borrowed books data
        "borrowed_books": [
            {
                "id": 1,
                "title": "Python Programming",
                "borrow_date": "2024-02-01",
                "due_date": "2024-02-15",
                "status": "Active"
            },
            {
                "id": 2,
                "title": "Data Structures",
                "borrow_date": "2024-01-20",
                "due_date": "2024-02-03",
                "status": "Overdue"
            }
        ],
        # Dummy transaction history
        "transactions": [
            {
                "id": 1,
                "type": "Borrow",
                "book_title": "Python Programming",
                "date": "2024-02-01",
                "fee": 150
            },
            {
                "id": 2,
                "type": "Return",
                "book_title": "JavaScript Basics",
                "date": "2024-01-25",
                "fee": 0
            }
        ]
    }
    
    return templates.TemplateResponse("admin/member_detail.html", member_data)

@router.get("/books", response_class=HTMLResponse)
@login_required
async def admin_view_books(
    request: Request, 
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    books_data = {
        "request": request,
        "total_books": 150,
        "available_books": 120,
        "borrowed_books": 30,
        "books": [
            {
                "id": 1,
                "title": "Python Programming",
                "author": "John Smith",
                "isbn": "978-1234567890",
                "category": "Programming",
                "status": "Available",
                "copies": 5,
                "available_copies": 3
            },
            {
                "id": 2,
                "title": "Data Science Basics",
                "author": "Jane Doe",
                "isbn": "978-0987654321",
                "category": "Data Science",
                "status": "Available",
                "copies": 3,
                "available_copies": 1
            },
            {
                "id": 3,
                "title": "Web Development",
                "author": "Mike Johnson",
                "isbn": "978-5432109876",
                "category": "Programming",
                "status": "All Borrowed",
                "copies": 2,
                "available_copies": 0
            }
        ]
    }
    return templates.TemplateResponse("admin/books.html", books_data)

@router.get("/books/{book_id}", response_class=HTMLResponse)
@login_required
async def admin_view_book_detail(
    request: Request, 
    book_id: int, 
    current_user: dict = Depends(get_current_user)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)

    book_data = {
        "request": request,
        "book": {
            "id": book_id,
            "title": "Python Programming",
            "author": "John Smith",
            "isbn": "978-1234567890",
            "publisher": "Tech Publications",
            "publication_year": 2023,
            "category": "Programming",
            "description": "A comprehensive guide to Python programming language...",
            "copies": 5,
            "available_copies": 3,
            "location": "Shelf A-12",
            "price": 599,
            "added_date": "2024-01-15"
        },
        "current_borrowers": [
            {
                "member_id": 1,
                "name": "Alice Brown",
                "borrow_date": "2024-02-01",
                "due_date": "2024-02-15",
                "status": "Active"
            },
            {
                "member_id": 2,
                "name": "Bob Wilson",
                "borrow_date": "2024-01-25",
                "due_date": "2024-02-08",
                "status": "Overdue"
            }
        ],
        "borrow_history": [
            {
                "member_name": "Charlie Davis",
                "borrow_date": "2023-12-15",
                "return_date": "2023-12-30",
                "status": "Returned"
            },
            {
                "member_name": "David Miller",
                "borrow_date": "2023-11-20",
                "return_date": "2023-12-05",
                "status": "Returned"
            }
        ]
    }
    return templates.TemplateResponse("admin/book_detail.html", book_data)

@router.get("/profile", response_class=HTMLResponse)
@login_required
async def admin_profile(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if user["role"] != UserRole.ADMIN.value:
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

