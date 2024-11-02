from sqlalchemy import Column, Integer, LargeBinary, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from .connection import Base

# Updated Enum
class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"

# Base Mixin for common columns
class BaseMixin:
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

class User(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {'comment': 'Stores user information including library members and administrators'}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255))
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.MEMBER)
    face_embedding = Column(LargeBinary, nullable=True)

    # Relationships
    borrowed_books = relationship("BookLoan", back_populates="user")

class Book(Base, BaseMixin):
    __tablename__ = "books"
    __table_args__ = {'comment': 'Contains information about books in the library inventory'}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    isbn = Column(String(13), unique=True, index=True)
    author = Column(String(100), nullable=False)
    publisher = Column(String(100))
    publication_year = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    
    # Relationships
    category = relationship("Category", back_populates="books")
    loans = relationship("BookLoan", back_populates="book")

class Category(Base, BaseMixin):
    __tablename__ = "categories"
    __table_args__ = {'comment': 'Book categories or genres for organization'}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))

    # Relationships
    books = relationship("Book", back_populates="category")

class BookLoan(Base, BaseMixin):
    __tablename__ = "book_loans"
    __table_args__ = {'comment': 'Tracks book borrowing transactions including due dates and returns'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    borrowed_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    due_date = Column(DateTime, nullable=False)
    returned_date = Column(DateTime)
    fine_amount = Column(Integer, default=0)  # Store fine in cents/paise
    is_returned = Column(Boolean, default=False)

    # Relationships
    user = relationship("User", back_populates="borrowed_books")
    book = relationship("Book", back_populates="loans")

class Fine(Base, BaseMixin):
    __tablename__ = "fines"
    __table_args__ = {'comment': 'Records fines for overdue books and their payment status'}

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(Integer, ForeignKey('book_loans.id'), nullable=False)
    amount = Column(Integer, nullable=False)  # Store fine in cents/paise
    paid_date = Column(DateTime)
    is_paid = Column(Boolean, default=False)

    # Relationships
    loan = relationship("BookLoan") 