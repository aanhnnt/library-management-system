from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.models import User, FavoriteBook, Book, BorrowingBook
from app.database.schemas import UserRole
from app.database.connection import get_db
from app.routers.auth import get_current_user
from app.utils.auth import login_required
from app.utils.dashboard import *
from datetime import datetime, timedelta

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
    # Get categories for dropdown
    categories = get_categories(db)
    
    dashboard_data = {
        "request": request,
        "stats": stats,
        "categories": categories,
        "search_results": None,
    }

    return templates.TemplateResponse("member/dashboard.html", dashboard_data)

@router.post("/dashboard", response_class=HTMLResponse)
@login_required
async def search_books(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    
    form = await request.form()
    title = form.get("searcht", "")
    author = form.get("searcha", "")
    category_id = form.get("category", "")
    
    # Calculate dashboard stats
    stats = calculate_member_stats(current_user["id"], db)
    # Get categories for dropdown
    categories = get_categories(db)
    # Get search results
    search_results = search_books_by_criteria(db, title, author, category_id)
    favorite_books = get_favorite_books(db, current_user["id"])
    favorite_book_ids = [book["id"] for book in favorite_books]
    
    dashboard_data = {
        "request": request,
        "stats": stats,
        "categories": categories,
        "search_results": search_results,
        "favorite_book_ids": favorite_book_ids
    }

    return templates.TemplateResponse("member/dashboard.html", dashboard_data)

@router.get("/borrowed", response_class=HTMLResponse)
@login_required
async def member_favorites(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    books = get_borrowed_books(db, current_user["id"])
    return templates.TemplateResponse("member/borrowed_books.html", {"request": request, "books": books})

@router.get("/overdued", response_class=HTMLResponse)
@login_required
async def member_overdued(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    books = get_overdue_books(db, current_user["id"])
    return templates.TemplateResponse("member/overdue_books.html", {"request": request, "books": books})

@router.get("/favorites", response_class=HTMLResponse)
@login_required
async def member_favorites(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    books = get_favorite_books(db, current_user["id"])
    return templates.TemplateResponse("member/favorite_books.html", {"request": request, "books": books})

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

@router.post("/favorites/{book_id}")
@login_required
async def add_favorite(
    request: Request,
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    try:
        add_favorite_book(db, book_id, current_user["id"])  # Add await here
        return {"status": "success", "message": "Book added to favorites"}
    except ValueError as e:
        return {"status": "error", "message": str(e)}

@router.delete("/favorites/{book_id}")
@login_required
async def delete_favorite(
    request: Request,
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    try:
        favorite = db.query(FavoriteBook).filter(
            FavoriteBook.book_id == book_id,
            FavoriteBook.user_id == current_user["id"]
        ).first()
        
        if favorite:
            db.delete(favorite)
            db.commit()
            return {"status": "success"}
        return {"status": "error", "message": "Favorite not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/borrow/{book_id}", response_class=HTMLResponse)
@login_required
async def borrow_book_form(
    request: Request,
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return RedirectResponse(url="/member/dashboard", status_code=303)
        
    return templates.TemplateResponse(
        "member/borrow_book.html", 
        {
            "request": request,
            "book": book,
            "min_date": datetime.now().strftime("%Y-%m-%d"),
            "max_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        }
    )

@router.post("/borrow/{book_id}", response_class=HTMLResponse)
@login_required
async def borrow_book(
    request: Request,
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
        
    form = await request.form()
    borrow_date = datetime.strptime(form.get("borrow_date"), "%Y-%m-%d")
    due_date = datetime.strptime(form.get("due_date"), "%Y-%m-%d")
    
    try:
        # Check if book is available
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book or book.available_copies <= 0:
            raise ValueError("Book is not available for borrowing")
            
        # Create new borrowing record
        new_borrow = BorrowingBook(
            user_id=current_user["id"],
            book_id=book_id,
            borrow_date=borrow_date,
            due_date=due_date,
            status=BorrowStatus.BORROWED
        )
        
        # Update book available copies
        book.available_copies -= 1
        
        db.add(new_borrow)
        db.commit()
        
        return RedirectResponse(url="/member/borrowed", status_code=303)
        
    except ValueError as e:
        return templates.TemplateResponse(
            "member/borrow_book.html",
            {
                "request": request,
                "book": book,
                "min_date": datetime.now().strftime("%Y-%m-%d"),
                "max_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
                "error": str(e)
            }
        )

@router.post("/return/{borrowing_id}")
@login_required
async def return_book(
    request: Request,
    borrowing_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return {"status": "error", "message": "Unauthorized"}
        
    try:
        # Find the borrowing record
        borrow_record = db.query(BorrowingBook).filter(
            BorrowingBook.id == borrowing_id,
            BorrowingBook.user_id == current_user["id"],
            BorrowingBook.status.in_([BorrowStatus.BORROWED, BorrowStatus.OVERDUE])
        ).first()
        
        if not borrow_record:
            return {"status": "error", "message": "Borrowing record not found"}
            
        # Update book available copies
        book = db.query(Book).filter(Book.id == borrow_record.book_id).first()
        book.available_copies += 1
        
        # Update borrowing record
        borrow_record.return_date = datetime.now()
        borrow_record.status = BorrowStatus.RETURNED
        
        db.commit()
        
        return {"status": "success", "message": "Book returned successfully"}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/books/{book_id}", response_class=HTMLResponse)
@login_required
async def member_view_book_detail(
    request: Request, 
    book_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)

    # Get book and stock details
    book, stock = get_book_details(db, book_id)
    if not book:
        return RedirectResponse(url="/member/dashboard", status_code=303)
        
    # Get transaction history
    transactions = get_user_book_transactions(db, book_id, current_user["id"])

    return templates.TemplateResponse(
        "member/book_detail.html",
        {
            "request": request,
            "book": book,
            "stock": stock,
            "trans": transactions
        }
    )

@router.post("/borrowed", response_class=HTMLResponse)
@login_required
async def search_borrowed_books(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    
    form = await request.form()
    title = form.get("searcht", "")
    author = form.get("searcha", "")
    
    books = get_borrowed_books(db, current_user["id"], title, author)
    return templates.TemplateResponse("member/borrowed_books.html", {"request": request, "books": books})

@router.post("/favorites", response_class=HTMLResponse)
@login_required
async def search_favorite_books(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    
    form = await request.form()
    title = form.get("searcht", "")
    author = form.get("searcha", "")
    
    books = get_favorite_books(db, current_user["id"], title, author)
    return templates.TemplateResponse("member/favorite_books.html", {"request": request, "books": books})

@router.post("/overdue", response_class=HTMLResponse)
@login_required
async def search_overdue_books(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.MEMBER.value:
        return RedirectResponse(url="/", status_code=303)
    
    form = await request.form()
    title = form.get("searcht", "")
    author = form.get("searcha", "")
    
    books = get_overdue_books(db, current_user["id"], title, author)
    return templates.TemplateResponse("member/overdue_books.html", {"request": request, "books": books})

