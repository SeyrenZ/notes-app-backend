from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    profile_picture: Optional[str] = None

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