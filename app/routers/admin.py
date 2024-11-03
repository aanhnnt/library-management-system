from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.schemas import UserRole
from app.routers.auth import get_current_user
from app.utils.auth import login_required
from app.database.models import User
from app.database.connection import get_db
from datetime import datetime, timezone
from app.database.models import BorrowingBook, Book, Category, Author
from app.utils.dashboard import *
from typing import Optional

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard", response_class=HTMLResponse)
@login_required
async def admin_dashboard(
    request: Request, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    # Get dashboard statistics from database
    stats = calculate_admin_stats(db)
    
    # Get recent transactions
    recent_transactions = db.query(BorrowingBook, Book).join(Book).order_by(BorrowingBook.created_at.desc()).limit(5).all()

    # Format transactions for template
    formatted_transactions = [
        (
            {
                "id": trans.id,
                "borrowed_date": (datetime.now(timezone.utc) - trans.created_at.replace(tzinfo=timezone.utc)).seconds // 60,  # Minutes ago
                "rent_fee": trans.book.rent_fee,
                "title": book.title
            }
        )
        for trans, book in recent_transactions
    ]
    
    dashboard_data = {
        "request": request,
        "borrowed_books": stats["total_borrowed"],
        "total_books": stats["total_books"],
        "total_rent_current_month": stats["total_rent_current_month"],
        "total_members": stats["total_members"],
        "recent_transactions": formatted_transactions
    }
    
    return templates.TemplateResponse("admin/dashboard.html", dashboard_data)

@router.get("/members", response_class=HTMLResponse)
@router.post("/members", response_class=HTMLResponse)
@login_required
async def admin_view_members(
    request: Request,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
    search_name: Optional[str] = None,
    search_email: Optional[str] = None,
    status: Optional[str] = None,
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    # Get form data if POST request
    if request.method == "POST":
        form = await request.form()
        search_name = form.get("search_name")
        search_email = form.get("search_email")
        status = form.get("status")
    
    query = db.query(User).filter(User.role == UserRole.MEMBER.value)
    
    if search_name:
        search_term = f"%{search_name}%"
        query = query.filter(
            or_(
                User.first_name.ilike(search_term),
                User.last_name.ilike(search_term)
            )
        )
    
    if search_email:
        query = query.filter(User.email.ilike(f"%{search_email}%"))
        
    if status:
        is_deleted = status == "inactive"
        query = query.filter(User.is_deleted == is_deleted)
        
    members = query.all()
    
    return templates.TemplateResponse(
        "admin/members.html", 
        {
            "request": request, 
            "members": members,
            "search_name": search_name,
            "search_email": search_email,
            "status": status
        }
    )

@router.get("/members/{member_id}", response_class=HTMLResponse)
@login_required
async def admin_view_member_detail(
    request: Request,
    member_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)

    member = db.query(User).filter(User.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    # Get member's transactions
    transactions = get_member_transactions(db, member_id)

    # Calculate outstanding debt
    outstanding_debt = sum(
        trans.total_fee 
        for trans in transactions 
        if not trans.return_date
    )

    return templates.TemplateResponse(
        "admin/member_detail.html",
        {
            "request": request,
            "member": member,
            "transactions": transactions,
            "outstanding_debt": outstanding_debt
        }
    )

@router.get("/books", response_class=HTMLResponse)
@login_required
async def admin_view_books(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    books = db.query(Book).all()
    categories = db.query(Category).all()
    authors = db.query(Author).all()
    
    return templates.TemplateResponse(
        "admin/books.html",
        {
            "request": request,
            "books": books,
            "categories": categories,
            "authors": authors
        }
    )

@router.post("/books", response_class=HTMLResponse)
@login_required
async def search_books(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    form = await request.form()
    title = form.get("searcht", "")
    author = form.get("searcha", "")
    category_id = form.get("category", "")
    
    books = search_books_by_criteria(db, title, author, category_id)
    categories = db.query(Category).all()
    return templates.TemplateResponse(
        "admin/books.html", 
        {
            "request": request, 
            "books": books,
            "categories": categories,
            "selected_category": category_id
        }
    )

@router.get("/books/{book_id}", response_class=HTMLResponse)
@login_required
async def admin_view_book_detail(
    request: Request, 
    book_id: int, 
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)

    # Get book and stock details
    book, stock = get_book_details(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    # Get all transactions for this book
    transactions = get_book_transactions(db, book_id)
    
    # Get current borrowers
    current_borrowers = [tran for tran in transactions if tran.status in [BorrowStatus.BORROWED.value, BorrowStatus.OVERDUE.value]]

    return templates.TemplateResponse(
        "admin/book_detail.html",
        {
            "request": request,
            "book": book,
            "stock": stock,
            "transactions": transactions,
            "current_borrowers": current_borrowers
        }
    )

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

@router.get("/edit_book/{book_id}", response_class=HTMLResponse)
@login_required
async def edit_book(
    request: Request,
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)   
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
        
    # Get all categories
    categories = get_categories(db)
    
    return templates.TemplateResponse(
        "admin/edit_book.html",
        {
            "request": request, 
            "book": book,
            "categories": categories
        }
    )

@router.post("/edit_book/{book_id}", response_class=HTMLResponse)
@login_required
async def update_book(
    request: Request,
    book_id: int,
    title: str = Form(...),
    author: str = Form(...),
    isbn: str = Form(...),
    category: int = Form(...),
    total_copies: int = Form(...),
    rent_fee: float = Form(...),
    late_fee: float = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    try:
        # Check if book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        
        # Check if author exists
        author_obj = db.query(Author).filter(Author.name == author).first()
        if not author_obj:
            # Get data for re-rendering the form
            authors = [{
                "id": author.id,
                "name": author.name
            } for author in db.query(Author).all()]
            categories = [{
                "id": category.id,
                "name": category.name
            } for category in db.query(Category).all()]
            
            return templates.TemplateResponse(
                "admin/edit_book.html",
                {
                    "request": request,
                    "book": book,
                    "authors": authors,
                    "categories": categories,
                    "error": f"Author '{author}' does not exist. Please add the author first."
                },
                status_code=400
            )

        # Update book details
        book.title = title
        book.author_id = author_obj.id
        book.isbn = isbn
        book.category_id = category
        book.total_copies = total_copies
        book.rent_fee = rent_fee
        book.late_fee = late_fee
        
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/books?success=Book updated successfully",
            status_code=303
        )
        
    except Exception as e:
        # Get data for re-rendering the form
        authors = [{
            "id": author.id,
            "name": author.name
        } for author in db.query(Author).all()]
        categories = [{
            "id": category.id,
            "name": category.name
        } for category in db.query(Category).all()]
        
        return templates.TemplateResponse(
            "admin/edit_book.html",
            {
                "request": request,
                "book": book,
                "authors": authors,
                "categories": categories,
                "error": f"Failed to update book: {str(e)}"
            },
            status_code=400
        )

@router.get("/delete_book/{book_id}")
@login_required
async def delete_book(
    request: Request,
    book_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    db.delete(book)
    db.commit()
    return RedirectResponse(url="/admin/books", status_code=303)

@router.post("/members/{member_id}/deactivate", response_class=JSONResponse)
@login_required
async def deactivate_member(
    request: Request,  # Thêm tham số này
    member_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    member = db.query(User).filter(User.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if member.is_deleted:
        raise HTTPException(status_code=400, detail="Member is already deactivated")
    
    member.is_deleted = True
    try:
        db.commit()
        return JSONResponse({"status": "success", "message": "Member deactivated successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/members/{member_id}/activate", response_class=JSONResponse)
@login_required
async def activate_member(
    request: Request,
    member_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    member = db.query(User).filter(User.id == member_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
        
    if not member.is_deleted:
        raise HTTPException(status_code=400, detail="Member is already active")
    
    member.is_deleted = False
    try:
        db.commit()
        return JSONResponse({"status": "success", "message": "Member activated successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings", response_class=HTMLResponse)
@login_required
async def admin_settings(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
        
    authors = db.query(Author).all()
    categories = db.query(Category).all()
    
    return templates.TemplateResponse(
        "admin/settings.html",
        {
            "request": request,
            "authors": authors,
            "categories": categories
        }
    )

@router.post("/settings/add-author", response_class=JSONResponse)
@login_required
async def add_author(
    request: Request,
    name: str = Form(...),
    biography: Optional[str] = Form(None),
    birth_date: Optional[str] = Form(None),
    nationality: Optional[str] = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        # Convert birth_date string to datetime if provided
        birth_date_obj = None
        if birth_date:
            try:
                birth_date_obj = datetime.strptime(birth_date, '%Y-%m-%d')
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid birth date format")

        author = Author(
            name=name,
            biography=biography,
            birth_date=birth_date_obj,
            nationality=nationality
        )
        db.add(author)
        db.commit()
        return JSONResponse({"status": "success", "message": "Author added successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings/add-category", response_class=JSONResponse)
@login_required 
async def add_category(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    try:
        category = Category(
            name=name,
            description=description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(category)
        db.commit()
        return JSONResponse({"status": "success", "message": "Category added successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/settings/delete-author/{author_id}", response_class=JSONResponse)
@login_required
async def delete_author(
    request: Request,
    author_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
        
    try:
        db.delete(author)
        db.commit()
        return JSONResponse({"status": "success", "message": "Author deleted successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/settings/delete-category/{category_id}", response_class=JSONResponse)
@login_required
async def delete_category(
    request: Request,
    category_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        raise HTTPException(status_code=403, detail="Not authorized")
        
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
        
    try:
        db.delete(category)
        db.commit()
        return JSONResponse({"status": "success", "message": "Category deleted successfully"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/add_book", response_class=HTMLResponse)
@login_required
async def add_book_form(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    authors = db.query(Author).all()
    categories = db.query(Category).all()
    
    return templates.TemplateResponse(
        "admin/add_book.html",
        {
            "request": request,
            "authors": authors,
            "categories": categories
        }
    )

@router.post("/add_book", response_class=HTMLResponse)
@login_required
async def add_book(
    request: Request,
    title: str = Form(...),
    author: int = Form(...),
    isbn: str = Form(...),
    category: int = Form(...),
    total_copies: int = Form(...),
    rent_fee: float = Form(...),
    late_fee: float = Form(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user["role"] != UserRole.ADMIN.value:
        return RedirectResponse(url="/", status_code=302)
    
    try:
        # Check if ISBN already exists
        existing_book = db.query(Book).filter(Book.isbn == isbn).first()
        if existing_book:
            raise ValueError("A book with this ISBN already exists")

        # Create new book
        new_book = Book(
            title=title,
            author_id=author,
            isbn=isbn,
            category_id=category,
            total_copies=total_copies,
            available_copies=total_copies,
            rent_fee=rent_fee,
            late_fee=late_fee
        )
        
        db.add(new_book)
        db.commit()
        
        return RedirectResponse(
            url=f"/admin/books?success=Book added successfully",
            status_code=303
        )
        
    except Exception as e:
        authors = db.query(Author).all()
        categories = db.query(Category).all()
        
        return templates.TemplateResponse(
            "admin/add_book.html",
            {
                "request": request,
                "authors": authors,
                "categories": categories,
                "error_message": str(e)
            }
        )