from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_

from app.database.models import Author, Book, BorrowStatus, BorrowingBook, Category, FavoriteBook, User, UserRole

def calculate_member_stats(user_id: int, db: Session):
    # Ensure all datetime comparisons are timezone-aware
    current_time = datetime.now(timezone.utc)
    
    # Get all borrowing records for the user
    borrowed_books = db.query(BorrowingBook).filter(BorrowingBook.user_id == user_id).all()
    
    total_fee = sum(
        borrowed_book.book.rent_fee * (borrowed_book.due_date.replace(tzinfo=timezone.utc) - borrowed_book.borrow_date.replace(tzinfo=timezone.utc)).days +
        borrowed_book.book.late_fee * (current_time - borrowed_book.due_date.replace(tzinfo=timezone.utc)).days
        for borrowed_book in borrowed_books
        if borrowed_book.due_date.replace(tzinfo=timezone.utc) < current_time  # Make timezone-aware before comparison
    )
    
    borrowed_books_count = db.query(BorrowingBook).filter(BorrowingBook.user_id == user_id, BorrowingBook.status == BorrowStatus.BORROWED).count()
    favorite_books_count = db.query(FavoriteBook).filter(FavoriteBook.user_id == user_id).count()
    overdue_books_count = db.query(BorrowingBook).filter(BorrowingBook.user_id == user_id, BorrowingBook.status == BorrowStatus.OVERDUE).count()
    
    return {
        "total_borrowed": borrowed_books_count,
        "total_favorites": favorite_books_count,
        "overdue_books": overdue_books_count,
        "total_fee": total_fee
    }

def calculate_admin_stats(db: Session):
    # Get current month and year with timezone awareness
    current_time = datetime.now(timezone.utc)
    current_month = current_time.month
    current_year = current_time.year
    
    # Get all rentals for current month
    current_month_rentals = db.query(BorrowingBook).filter(
        or_(
            extract('month', BorrowingBook.borrow_date) == current_month,
            extract('month', BorrowingBook.return_date) == current_month,
            extract('month', BorrowingBook.due_date) == current_month
        ),
        extract('year', BorrowingBook.borrow_date) == current_year,
        extract('year', BorrowingBook.return_date) == current_year,
        extract('year', BorrowingBook.due_date) == current_year
    ).all()

    # Calculate total earnings for current month
    total_earnings = 0
    for rental in current_month_rentals:
        if rental.return_date:  # Only count completed rentals
            # Make all datetime objects timezone-aware
            start_of_month = datetime(current_year, current_month, 1, tzinfo=timezone.utc)
            end_of_month = (start_of_month + relativedelta(months=1)).replace(day=1)
            
            borrow_date = rental.borrow_date.replace(tzinfo=timezone.utc)
            return_date = rental.return_date.replace(tzinfo=timezone.utc) if rental.return_date else current_time

            # Adjust dates to fit within the current month
            adjusted_borrow_date = max(borrow_date, start_of_month)
            adjusted_due_date = min(return_date, end_of_month)

            fees = calculate_book_fees(
                adjusted_borrow_date,
                rental.due_date.replace(tzinfo=timezone.utc),
                return_date,
                rental.book.rent_fee,
                rental.book.late_fee
            )
            total_earnings += fees['total_fee']

    # Calculate other stats
    total_books = db.query(Book).count()
    total_members = db.query(User).filter(User.role == UserRole.MEMBER).count()
    total_borrowed = db.query(BorrowingBook).filter(BorrowingBook.status == BorrowStatus.BORROWED).count()
    
    return {
        "total_books": total_books,
        "total_members": total_members,
        "total_borrowed": total_borrowed,
        "total_rent_current_month": total_earnings
    }

def get_categories(db: Session):
    """Retrieve a limited number of categories from the database."""
    return db.query(Category).all()

def get_books(db: Session):
    """Retrieve all books"""
    query = db.query(Book)
    return query.all()

def calculate_book_fees(borrow_date: datetime, due_date: datetime, return_date: datetime | None, rent_fee: float, late_fee: float) -> dict:
    """Calculate rent fee and late fee for a book
    
    Args:
        borrow_date: Date the book was borrowed
        due_date: Date the book was due
        return_date: Date the book was returned (None if not returned yet)
        rent_fee: Daily rental fee
        late_fee: Daily late fee
    """
    # Ensure all dates are timezone-aware
    current_time = datetime.now(timezone.utc)
    borrow_date = borrow_date.replace(tzinfo=timezone.utc)
    due_date = due_date.replace(tzinfo=timezone.utc)
    end_date = return_date.replace(tzinfo=timezone.utc) if return_date else current_time
    
    # Calculate rental days (from borrow to due date)
    rent_days = (due_date - borrow_date).days if end_date > due_date else max(0, (end_date - borrow_date).days)
    
    # Calculate late days (from due date to return/current date)
    late_days = max(0, (end_date - due_date).days)
    
    # Calculate fees
    total_rent_fee = round(rent_fee * rent_days, 2)
    total_late_fee = round(late_fee * late_days, 2)
    
    return {
        "rent_days": rent_days,
        "late_days": late_days,
        "rent_fee": total_rent_fee,
        "late_fee": total_late_fee,
        "total_fee": total_rent_fee + total_late_fee
    }

def get_overdue_books(db: Session, user_id: int, title: str = "", author: str = ""):
    """Retrieve filtered overdue books"""
    query = db.query(BorrowingBook).filter(
        BorrowingBook.status == BorrowStatus.OVERDUE,
        BorrowingBook.user_id == user_id
    ).join(Book).join(Author)
    
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Author.name.ilike(f"%{author}%"))
        
    query = query.order_by(BorrowingBook.book_id)
    overdue_books = query.all()
    
    return [{
        "id": overdued.id,
        "book_id": overdued.book.id,
        "title": overdued.book.title,
        "author": overdued.book.author.name,
        "isbn": overdued.book.isbn,
        "category": overdued.book.category.name,
        "due_date": overdued.due_date,
        "borrow_date": overdued.borrow_date,
        "fees": calculate_book_fees(
            overdued.borrow_date,
            overdued.due_date,
            None,  # Not returned yet
            overdued.book.rent_fee,
            overdued.book.late_fee
        )
    } for overdued in overdue_books]

def get_borrowed_books(db: Session, user_id: int, title: str = "", author: str = ""):
    """Retrieve filtered borrowed books"""
    query = db.query(BorrowingBook).filter(
        BorrowingBook.status.in_([BorrowStatus.BORROWED, BorrowStatus.RETURNED]),
        BorrowingBook.user_id == user_id
    ).join(Book).join(Author)
    
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Author.name.ilike(f"%{author}%"))
        
    query = query.order_by(BorrowingBook.book_id)
    borrowed_books = query.all()
    
    return [{
        "id": borrowed.id,
        "book_id": borrowed.book.id,
        "title": borrowed.book.title,
        "author": borrowed.book.author.name,
        "isbn": borrowed.book.isbn,
        "category": borrowed.book.category.name,
        "due_date": borrowed.due_date,
        "borrow_date": borrowed.borrow_date,
        "return_date": borrowed.return_date,
        "status": borrowed.status,
        "fees": calculate_book_fees(
            borrowed.borrow_date,
            borrowed.due_date,
            borrowed.return_date,
            borrowed.book.rent_fee,
            borrowed.book.late_fee
        )
    } for borrowed in borrowed_books]

def get_favorite_books(db: Session, user_id: int, title: str = "", author: str = ""):
    """Retrieve filtered favorite books"""
    query = db.query(FavoriteBook).filter(
        FavoriteBook.user_id == user_id
    ).join(Book).join(Author)
    
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Author.name.ilike(f"%{author}%"))
        
    query = query.order_by(FavoriteBook.book_id)
    favorite_books = query.all()
    
    return [{
        "id": favorite_book.book.id,
        "title": favorite_book.book.title,
        "author": favorite_book.book.author.name,
        "isbn": favorite_book.book.isbn,
        "category": favorite_book.book.category.name,
        "total_copies": favorite_book.book.total_copies,
        "available_copies": favorite_book.book.available_copies,
        "added_date": favorite_book.created_at
    } for favorite_book in favorite_books]

def delete_favorite_book(db: Session, book_id: int, user_id: int):
    """Delete a favorite book for a user"""
    favorite = db.query(FavoriteBook).filter(
        FavoriteBook.book_id == book_id,
        FavoriteBook.user_id == user_id
    ).first()
    
    if not favorite:
        raise ValueError("Book not found in favorites")
        
    db.delete(favorite)
    db.commit()

def add_favorite_book(db: Session, book_id: int, user_id: int):
    """Add a favorite book for a user"""
    # Check if book exists
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise ValueError("Book not found")
    
    # Check if already in favorites
    existing = db.query(FavoriteBook).filter(
        FavoriteBook.book_id == book_id,
        FavoriteBook.user_id == user_id
    ).first()
    
    if existing:
        raise ValueError("Book already in favorites")
    
    new_favorite = FavoriteBook(
        book_id=book_id,
        user_id=user_id
    )
    db.add(new_favorite)
    db.commit()

def search_books_by_criteria(db: Session, title: str = "", author: str = "", category_id: str = ""):
    """Search books with filters for title, author name and category"""
    query = db.query(Book).join(Author)  # Join with Author table
    
    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if author:
        query = query.filter(Author.name.ilike(f"%{author}%"))  # Filter on Author.name
    if category_id and category_id.isdigit():
        query = query.filter(Book.category_id == int(category_id))
    
    books = query.all()
    return [{
        "id": book.id,
        "title": book.title,
        "author": book.author.name,  # Access author name through relationship
        "isbn": book.isbn,
        "category": book.category.name,
        "rent_fee": book.rent_fee,
        "copies": book.total_copies,
        "available_copies": book.available_copies
    } for book in books]

def get_book_details(db: Session, book_id: int):
    """Get book details and stock information"""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        return None, None
        
    # Get stock details
    total_borrowed = db.query(BorrowingBook).filter(
        BorrowingBook.book_id == book_id
    ).count()
    
    current_borrowed = db.query(BorrowingBook).filter(
        BorrowingBook.book_id == book_id,
        BorrowingBook.status == BorrowStatus.BORROWED
    ).count()
    
    stock = {
        "total_quantity": book.total_copies,
        "available_quantity": book.available_copies,
        "borrowed_quantity": current_borrowed,
        "total_borrowed": total_borrowed
    }
    
    return book, stock

def get_user_book_transactions(db: Session, book_id: int, user_id: int):
    """Get transaction history for a specific book and user"""
    trans =  db.query(BorrowingBook).filter(
        BorrowingBook.book_id == book_id,
        BorrowingBook.user_id == user_id
    ).order_by(BorrowingBook.borrow_date.desc()).all()

    for tran in trans:
        fee = calculate_book_fees(
            tran.borrow_date,
            tran.due_date,
            tran.return_date,
            tran.book.rent_fee,
            tran.book.late_fee
        )
        tran.rent_fee = fee["rent_fee"]
        tran.late_fee = fee["late_fee"]
        tran.total_fee = fee["total_fee"]
        tran.status = tran.status.value
    return trans

def get_book_transactions(db: Session, book_id: int):
    """Get transaction history for a specific book and user"""
    trans =  db.query(BorrowingBook).filter(
        BorrowingBook.book_id == book_id
    ).order_by(BorrowingBook.borrow_date.desc()).all()

    for tran in trans:
        fee = calculate_book_fees(
            tran.borrow_date,
            tran.due_date,
            tran.return_date,
            tran.book.rent_fee,
            tran.book.late_fee
        )
        tran.rent_fee = fee["rent_fee"]
        tran.late_fee = fee["late_fee"]
        tran.total_fee = fee["total_fee"]
        tran.status = tran.status.value
    return trans

def get_member_transactions(db: Session, member_id: int):
    """Get transaction history for a specific member"""
    """Get transaction history for a specific book and user"""
    trans =  db.query(BorrowingBook).filter(
        BorrowingBook.user_id == member_id
    ).order_by(BorrowingBook.borrow_date.desc()).all()

    for tran in trans:
        fee = calculate_book_fees(
            tran.borrow_date,
            tran.due_date,
            tran.return_date,
            tran.book.rent_fee,
            tran.book.late_fee
        )
        tran.rent_fee = fee["rent_fee"]
        tran.late_fee = fee["late_fee"]
        tran.total_fee = fee["total_fee"]
        tran.status = tran.status.value
    return trans

