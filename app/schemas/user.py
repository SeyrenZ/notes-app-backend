from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    username: str
    preferred_theme: Optional[str] = "light"
    preferred_font: Optional[str] = "sans-serif"

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    profile_picture: Optional[str] = None

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    preferred_theme: Optional[str] = None
    preferred_font: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Google OAuth related schemas
class GoogleAuthRequest(BaseModel):
    token: str

class OAuthUserCreate(BaseModel):
    email: str
    username: str
    google_id: str
    profile_picture: Optional[str] = None
    preferred_theme: Optional[str] = "light"
    preferred_font: Optional[str] = "sans-serif" 