from fastapi import APIRouter, Depends, HTTPException, Request, Form, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.database.connection import get_db
from app.database.models import User, UserRole
from app.utils.auth import get_password_hash, login_required, verify_password
from app.utils.face_recognition import FaceRecognition

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")

face_recognition = FaceRecognition()

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/auth/login"}
        )
    return user

@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request):
    return templates.TemplateResponse(
        "auth/signup.html", 
        {"request": request}
    )

@router.post("/signup", response_class=HTMLResponse)
async def signup(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    enable_face_id: bool = Form(False),
    db: Session = Depends(get_db)
):
    try:
        if password != confirm_password:
            return templates.TemplateResponse(
                "auth/signup.html",
                {"request": request, "error": "Passwords do not match", "email": email, "username": username}
            )

        # Check if username exists
        if db.query(User).filter(User.username == username).first():
            return templates.TemplateResponse(
                "auth/signup.html",
                {"request": request, "error": "Username already exists", "email": email}
            )

        # Check if email exists
        if db.query(User).filter(User.email == email).first():
            return templates.TemplateResponse(
                "auth/signup.html",
                {"request": request, "error": "Email already exists", "username": username}
            )

        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            username=username,
            hashed_password=hashed_password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Set session
        request.session["user"] = {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "role": new_user.role.value
        }

        # Redirect based on face ID preference
        if enable_face_id:
            return RedirectResponse(url="/auth/register-face", status_code=303)
        else:
            return RedirectResponse(url="/member/dashboard", status_code=303)

    except Exception as e:
        return templates.TemplateResponse(
            "auth/signup.html",
            {"request": request, "error": str(e), "email": email, "username": username}
        )

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        "auth/login.html", 
        {"request": request}
    )

@router.post("/login")
async def login(
    request: Request,
    username_or_email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        # Check if login is with email or username
        user = db.query(User).filter(
            or_(
                User.email == username_or_email,
                User.username == username_or_email
            )
        ).first()

        if not user:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "User does not exist",
                    "username_or_email": username_or_email
                }
            )
        
        if not verify_password(password, user.hashed_password):
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Incorrect password",
                    "username_or_email": username_or_email
                }
            )
        
        if user.is_deleted:
            return templates.TemplateResponse(
                "auth/login.html",
                {
                    "request": request,
                    "error": "Account is inactive",
                    "username_or_email": username_or_email
                }
            )
            
        request.session["user"] = {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role.value
        }
        
        # Redirect based on user role
        return RedirectResponse(url="/", status_code=303)
        
    except Exception as e:
        return templates.TemplateResponse(
            "auth/login.html",
            {
                "request": request,
                "error": "An error occurred during login",
                "username_or_email": username_or_email
            }
        )

@router.get("/logout")
async def logout(request: Request):
    # Xóa session khi logout
    request.session.clear()
    return RedirectResponse(
        url="/auth/login",
        status_code=303
    )

@router.post("/register-face")
@login_required
async def register_face(
    request: Request,
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        # Read image data
        image_data = await face_image.read()
        
        # Process and save face encoding
        success, message, encoding_bytes = await face_recognition.save_face_encoding(image_data, user["username"])
        
        if success:
            # Update user record with face encoding
            db_user = db.query(User).filter(User.id == user["id"]).first()
            if db_user:
                db_user.face_embedding = encoding_bytes
                db.commit()
                return {"success": True, "message": message}
        
        return {"success": False, "error": message}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.get("/register-face", response_class=HTMLResponse)
@login_required
async def register_face_page(request: Request):
    return templates.TemplateResponse(
        "auth/register_face.html",
        {"request": request}
    )

@router.post("/login-face")
async def login_face(
    request: Request,
    face_image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    try:
        image_data = await face_image.read()
        
        # Get all users with face embeddings
        users = db.query(User).filter(User.face_embedding.isnot(None)).all()
        
        for user in users:
            is_match = await face_recognition.verify_face(image_data, user.face_embedding)

            if not is_match:
                continue
            
            if is_match and user.is_deleted:
                return {"success": False, "error": "User account is inactive"}
                
            request.session["user"] = {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "role": user.role.value
            }
            return {"success": True, "redirect_url": "/"}
                
        return {"success": False, "error": "Face verification failed"}
    except Exception as e:
        print(f"Login error: {str(e)}")
        return {"success": False, "error": "Error during face verification"}

@router.post("/update-profile")
@login_required
async def update_profile(
    request: Request,
    first_name: str = Form(None),
    last_name: str = Form(None),
    phone: str = Form(None),
    address: str = Form(None),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    db_user = db.query(User).filter(User.id == user["id"]).first()
    
    if db_user:
        db_user.first_name = first_name
        db_user.last_name = last_name
        db_user.phone = phone
        db_user.address = address
        db.commit()
        
        return {"success": True, "message": "Profile updated successfully"}
    
    return {"success": False, "error": "User not found"}

@router.get("/change-password", response_class=HTMLResponse)
@login_required
async def change_password_page(request: Request):
    return templates.TemplateResponse(
        "auth/change_password.html",
        {"request": request}
    )

@router.post("/change-password")
@login_required
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    db_user = db.query(User).filter(User.id == user["id"]).first()
    
    if not verify_password(current_password, db_user.hashed_password):
        return {"success": False, "error": "Current password is incorrect"}
        
    if new_password != confirm_password:
        return {"success": False, "error": "New passwords do not match"}
        
    if len(new_password) < 8:
        return {"success": False, "error": "Password must be at least 8 characters long"}
    
    # Update password
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"success": True, "message": "Password updated successfully"}