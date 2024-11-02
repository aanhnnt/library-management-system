from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from fastapi import Request
from fastapi.responses import RedirectResponse
from functools import wraps
import os

# Configure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    # Set expiration
    if expires_delta:
        expire = datetime.now(datetime.now(timezone.utc)) + expires_delta
    else:
        expire = datetime.now(datetime.now(timezone.utc)) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt 

def login_required(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        # Check session or token

        user = request.session.get("user")
        
        if not user:
            # If not logged in, redirect to login page
            return RedirectResponse(
                url="/auth/login",
                status_code=303
            )
        
        # If logged in, continue processing the request
        return await func(request, *args, **kwargs)
    return wrapper