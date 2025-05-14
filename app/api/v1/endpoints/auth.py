from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import os
from dotenv import load_dotenv
from sqlalchemy import or_
import logging
from typing import Optional
import requests

from app.core.security import verify_password, get_password_hash, create_access_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, TokenData, GoogleAuthRequest, OAuthUserCreate, UserUpdate

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{os.getenv('API_V1_STR', '/api/v1')}/auth/token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM", "HS256")])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Attempting to register user with email: {user.email} and username: {user.username}")
    
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"Registration failed: Email {user.email} already registered")
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"Registration failed: Username {user.username} already taken")
        raise HTTPException(status_code=400, detail="Username already taken")
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"Successfully registered user: {user.username}")
    return db_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Login attempt for username/email: {form_data.username}")
    
    # Try to find user by username or email
    user = db.query(User).filter(
        or_(
            User.username == form_data.username,
            User.email == form_data.username
        )
    ).first()
    
    if not user:
        logger.warning(f"Login failed: User not found for username/email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: Invalid password for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    logger.info(f"Successful login for user: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

# NextAuth specific endpoints
@router.post("/nextauth/callback/credentials")
async def nextauth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        email = data.get("email")
        password = data.get("password")
        
        if not email or not password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email and password are required"
            )
        
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "id": str(user.id),
            "name": user.username,
            "email": user.email,
            "accessToken": access_token
        }
    except Exception as e:
        logger.error(f"NextAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

# Google OAuth endpoints for NextAuth
@router.post("/google/verify")
async def verify_google_token(auth_request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Verify Google ID token and return user info."""
    try:
        # Verify token with Google
        google_oauth_url = "https://www.googleapis.com/oauth2/v3/tokeninfo"
        params = {"id_token": auth_request.token}
        response = requests.get(google_oauth_url, params=params)
        
        if response.status_code != 200:
            logger.error(f"Google token verification failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Google token"
            )
        
        token_info = response.json()
        
        # Check if user with this Google ID already exists
        google_id = token_info.get("sub")
        email = token_info.get("email")
        
        user = db.query(User).filter(
            or_(
                User.google_id == google_id,
                User.email == email
            )
        ).first()
        
        if not user:
            # Create new user if not exists
            username = email.split("@")[0]  # Use part before @ as username
            base_username = username
            
            # Check if username exists, append numbers if needed
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                google_id=google_id,
                profile_picture=token_info.get("picture"),
                is_active=True,
                preferred_theme="light"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        elif not user.google_id:
            # Update existing email user with Google ID
            user.google_id = google_id
            user.profile_picture = token_info.get("picture")
            db.commit()
            db.refresh(user)
        
        # Create access token
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        return {
            "id": str(user.id),
            "name": user.username,
            "email": user.email,
            "picture": user.profile_picture,
            "accessToken": access_token
        }
        
    except Exception as e:
        logger.error(f"Google authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google authentication failed"
        )

@router.post("/nextauth/callback/google")
async def nextauth_google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle NextAuth Google callback."""
    try:
        # Log the raw request data for debugging
        request_body = await request.body()
        logger.info(f"NextAuth Google callback received raw data: {request_body}")
        
        data = await request.json()
        logger.info(f"NextAuth Google callback received parsed data: {data}")
        
        # Extract Google profile data sent by NextAuth
        # Handle different data structures that NextAuth might send
        if isinstance(data, dict):
            # Direct data
            google_id = data.get("id") or data.get("sub")
            email = data.get("email")
            name = data.get("name")
            picture = data.get("picture") or data.get("image")
        elif hasattr(data, "get"):
            # If data has a get method
            google_id = data.get("id") or data.get("sub")
            email = data.get("email")
            name = data.get("name")
            picture = data.get("picture") or data.get("image")
        else:
            # Try to access as object properties
            google_id = getattr(data, "id", None) or getattr(data, "sub", None)
            email = getattr(data, "email", None)
            name = getattr(data, "name", None)
            picture = getattr(data, "picture", None) or getattr(data, "image", None)
        
        # Look for nested objects like data.user or data.account
        if hasattr(data, "user") and not google_id:
            user_data = data.user
            google_id = getattr(user_data, "id", None) or getattr(user_data, "sub", None)
            email = getattr(user_data, "email", email)
            name = getattr(user_data, "name", name)
            picture = getattr(user_data, "picture", picture) or getattr(user_data, "image", picture)
        
        if isinstance(data, dict) and "user" in data and not google_id:
            user_data = data["user"]
            google_id = user_data.get("id") or user_data.get("sub") or google_id
            email = user_data.get("email") or email
            name = user_data.get("name") or name
            picture = user_data.get("picture") or user_data.get("image") or picture
        
        # If we have account data with providerAccountId
        if isinstance(data, dict) and "account" in data:
            account_data = data["account"]
            google_id = account_data.get("providerAccountId") or account_data.get("id") or google_id
        
        # For NextAuth specific structure
        if isinstance(data, dict) and "profile" in data:
            profile = data["profile"]
            google_id = profile.get("sub") or profile.get("id") or google_id
            email = profile.get("email") or email
            name = profile.get("name") or name
            picture = profile.get("picture") or profile.get("image") or picture
        
        logger.info(f"Extracted Google auth data: id={google_id}, email={email}, name={name}")
        
        if not google_id or not email:
            logger.error("Missing required fields: Google ID or email")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google ID and email are required"
            )
        
        # Check if user exists
        user = db.query(User).filter(
            or_(
                User.google_id == google_id,
                User.email == email
            )
        ).first()
        
        if not user:
            # Create new user
            logger.info(f"Creating new user for Google account: {email}")
            username = email.split("@")[0]  # Use part before @ as username
            base_username = username
            
            # Check if username exists, append numbers if needed
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            user = User(
                email=email,
                username=username,
                google_id=google_id,
                profile_picture=picture,
                is_active=True,
                preferred_theme="light"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"Created new user with ID: {user.id}, username: {user.username}")
        elif not user.google_id:
            # Update existing email user with Google ID
            logger.info(f"Updating existing user with Google ID: {user.id}, {user.username}")
            user.google_id = google_id
            user.profile_picture = picture
            db.commit()
            db.refresh(user)
            logger.info("User updated with Google ID")
        else:
            logger.info(f"User already exists: {user.id}, {user.username}")
        
        # Create access token
        logger.info("Generating access token")
        access_token_expires = timedelta(minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")))
        access_token = create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        
        response_data = {
            "id": str(user.id),
            "name": user.username,
            "email": user.email,
            "picture": user.profile_picture,
            "accessToken": access_token
        }
        logger.info(f"Successful Google authentication for: {user.username}")
        return response_data
        
    except Exception as e:
        logger.error(f"NextAuth Google callback error: {str(e)}")
        # Log the full exception details including traceback
        import traceback
        logger.error(f"Full exception details: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        ) 