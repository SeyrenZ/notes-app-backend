from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate
from app.api.v1.endpoints.auth import get_current_user

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    response = UserResponse.model_validate(current_user)
    response.is_oauth_user = bool(current_user.google_id)
    return response

@router.put("/me/preferences", response_model=UserResponse)
async def update_user_preferences(
    preferences: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update user preferences like theme."""
    logger.info(f"Updating preferences for user: {current_user.username}")
    
    # Update user fields that are provided
    for field, value in preferences.model_dump(exclude_unset=True).items():
        if value is not None:  # Only update if a value is provided
            setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"Preferences updated for user: {current_user.username}")
    response = UserResponse.model_validate(current_user)
    response.is_oauth_user = bool(current_user.google_id)
    return response 