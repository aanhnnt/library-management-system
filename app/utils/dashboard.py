from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database.models import BorrowStatus, BorrowingBook, FavoriteBook

def calculate_member_stats(user_id: int, db: Session):
    # Ensure all datetime comparisons are timezone-aware
    current_time = datetime.now(timezone.utc)
    
    # Get all borrowing records for the user
    borrowed_books = db.query(BorrowingBook).filter(BorrowingBook.user_id == user_id).all()
    
    total_fee = sum(
        book.rent_fee * (book.due_date.replace(tzinfo=timezone.utc) - book.borrow_date.replace(tzinfo=timezone.utc)).days +
        book.late_fee * (current_time - book.due_date.replace(tzinfo=timezone.utc)).days
        for book in borrowed_books
        if book.due_date.replace(tzinfo=timezone.utc) < current_time  # Make timezone-aware before comparison
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