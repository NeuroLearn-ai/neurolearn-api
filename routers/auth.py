from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from security import get_current_user

import models
import schemas
import security
from database import get_db

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)

# --------------------------------------------------------------------------
# 1. STANDARD EMAIL/PASSWORD REGISTRATION
# --------------------------------------------------------------------------
@router.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    # Hash password and save
    hashed_pwd = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email, 
        hashed_password=hashed_pwd, 
        provider="email"
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# --------------------------------------------------------------------------
# 2. STANDARD EMAIL/PASSWORD LOGIN
# --------------------------------------------------------------------------
@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    # 1. Find user by email
    result = await db.execute(select(models.User).where(models.User.email == form_data.username))
    user = result.scalars().first()
    
    # 2. Check if user exists and has a password
    # (If they signed up via Google, they might not have a password set)
    if user and user.provider == "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="This email is linked to a Google account. Please login with Google."
        )

    # 3. Verify password
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Generate JWT
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --------------------------------------------------------------------------
# 3. GOOGLE LOGIN (START FLOW)
# --------------------------------------------------------------------------
@router.get("/login/google")
async def login_google(request: Request):
    """
    Redirects the user's browser to the Google Login page.
    """
    # This URL must match EXACTLY what is in your Google Cloud Console
    redirect_uri = "http://localhost:8000/auth/callback" 
    return await security.oauth.google.authorize_redirect(request, redirect_uri)

# --------------------------------------------------------------------------
# 4. GOOGLE CALLBACK (FINISH FLOW)
# --------------------------------------------------------------------------
@router.get("/callback")
async def auth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    """
    Google redirects back here with a code. 
    We exchange it for a token, get user info, and log them in.
    """
    try:
        # A. Securely Exchange Code for Google Token
        token = await security.oauth.google.authorize_access_token(request)
        
        # B. Get User Info from the token
        # Note: 'userinfo' is automatically parsed by Authlib from the id_token
        user_info = token.get('userinfo')
        
        # Fallback manual fetch if userinfo is missing (rare)
        if not user_info:
            user_info = await security.oauth.google.userinfo(token=token)
            
        email = user_info.get('email')
        
        # C. Check DB (Hybrid Logic)
        result = await db.execute(select(models.User).where(models.User.email == email))
        user = result.scalars().first()

        if not user:
            # CASE A: New User -> Create account automatically (No password)
            user = models.User(
                email=email, 
                hashed_password=None, 
                provider="google"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # D. Generate OUR JWT (This is what the Frontend uses)
        access_token = security.create_access_token(data={"sub": user.email})
        
        # E. Redirect back to Frontend Dashboard with the token
        # We pass the token in the URL query params
        frontend_url = f"http://localhost:3000/auth/google-success?token={access_token}"
        return RedirectResponse(url=frontend_url)

    except Exception as e:
        print(f"OAuth Error: {e}")
        # Redirect to a frontend error page
        return RedirectResponse(url="http://localhost:3000/auth/error")
    

# --------------------------------------------------------------------------
# 5. Get Current User Info
# --------------------------------------------------------------------------
@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user