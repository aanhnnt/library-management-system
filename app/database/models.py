from sqlalchemy import Column, Float, Integer, LargeBinary, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database.connection import Base
import enum

class UserRole(enum.Enum):
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"
class BorrowStatus(enum.Enum):
    BORROWED = "BORROWED"
    RETURNED = "RETURNED"
    OVERDUE = "OVERDUE"
    LOST = "LOST"

# Base Mixin for common columns
class BaseMixin:
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)

class User(Base, BaseMixin):
    __tablename__ = "users"
    __table_args__ = {'comment': 'Stores user information including library members and administrators'}

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
    borrowed_books = relationship("BorrowingBook", back_populates="user")
    favorites = relationship("FavoriteBook", back_populates="user")

class Author(Base, BaseMixin):
    __tablename__ = "authors"
    __table_args__ = {'comment': 'Contains information about book authors'}

    name = Column(String(100), nullable=False)
    biography = Column(Text, nullable=True)
    birth_date = Column(DateTime, nullable=True)
    nationality = Column(String(50), nullable=True)

    # Relationships
    books = relationship("Book", back_populates="author")

class Book(Base, BaseMixin):
    __tablename__ = "books"
    __table_args__ = {'comment': 'Contains information about books in the library inventory'}

    title = Column(String(200), nullable=False)
    isbn = Column(String(13), unique=True, index=True)
    author_id = Column(Integer, ForeignKey('authors.id'))
    publisher = Column(String(100))
    publication_year = Column(Integer)
    category_id = Column(Integer, ForeignKey('categories.id'))
    rent_fee = Column(Float, default=0.0)
    late_fee = Column(Float, default=0.0)
    total_copies = Column(Integer, default=1)
    available_copies = Column(Integer, default=1)
    
    # Relationships
    category = relationship("Category", back_populates="books")
    borrowing_books = relationship("BorrowingBook", back_populates="book")
    favorites = relationship("FavoriteBook", back_populates="book")
    author = relationship("Author", back_populates="books")

class Category(Base, BaseMixin):
    __tablename__ = "categories"
    __table_args__ = {'comment': 'Book categories or genres for organization'}

    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(200))

    # Relationships
    books = relationship("Book", back_populates="category")

class BorrowingBook(Base, BaseMixin):
    __tablename__ = "borrowing_books"
    __table_args__ = {'comment': 'Stores user borrowed books'}

    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    borrow_date = Column(DateTime, default=datetime.now(timezone.utc))
    due_date = Column(DateTime)
    return_date = Column(DateTime, nullable=True)
    status = Column(SQLEnum(BorrowStatus), default=BorrowStatus.BORROWED)
    
    user = relationship("User", back_populates="borrowed_books")
    book = relationship("Book", back_populates="borrowing_books")

class FavoriteBook(Base, BaseMixin):
    __tablename__ = "favorite_books"
    __table_args__ = {'comment': 'Stores user favorites books'}
    
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    
    user = relationship("User", back_populates="favorites")
    book = relationship("Book", back_populates="favorites")