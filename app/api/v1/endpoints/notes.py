from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.session import get_db
from app.models.note import Note, Tag
from app.models.user import User
from app.schemas.note import NoteCreate, NoteUpdate, NoteResponse, TagCreate, TagResponse
from app.api.v1.endpoints.auth import get_current_user

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=NoteResponse)
def create_note(
    note: NoteCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new note for the current user."""
    logger.info(f"Creating new note for user: {current_user.username}")
    
    db_note = Note(
        user_id=current_user.id,
        title=note.title,
        content=note.content,
        is_archived=note.is_archived,
        theme_color=note.theme_color,
        font_family=note.font_family
    )
    
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    
    logger.info(f"Note created with ID: {db_note.id}")
    return db_note

@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing note."""
    logger.info(f"Updating note ID: {note_id} for user: {current_user.username}")
    
    db_note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not db_note:
        logger.warning(f"Note not found or not owned by user: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to edit it"
        )
    
    # Update note fields
    for field, value in note.model_dump(exclude_unset=True).items():
        setattr(db_note, field, value)
    
    db.commit()
    db.refresh(db_note)
    
    logger.info(f"Note updated successfully: {note_id}")
    return db_note

@router.post("/{note_id}/tags", response_model=NoteResponse)
def add_tags_to_note(
    note_id: int,
    tags: List[TagCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add tags to a note."""
    logger.info(f"Adding tags to note ID: {note_id}")
    
    # Verify note exists and belongs to the current user
    note = db.query(Note).filter(Note.id == note_id, Note.user_id == current_user.id).first()
    if not note:
        logger.warning(f"Note not found or not owned by user: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to edit it"
        )
    
    # Process each tag
    for tag_data in tags:
        # Check if tag already exists
        existing_tag = db.query(Tag).filter(Tag.name == tag_data.name).first()
        
        if existing_tag:
            tag = existing_tag
        else:
            # Create new tag
            tag = Tag(name=tag_data.name)
            db.add(tag)
            db.commit()
            db.refresh(tag)
        
        # Add tag to note if not already added
        if tag not in note.tags:
            note.tags.append(tag)
    
    db.commit()
    db.refresh(note)
    
    logger.info(f"Tags added to note ID: {note_id}")
    return note

@router.get("/", response_model=List[NoteResponse])
def get_user_notes(
    archived: Optional[bool] = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all notes for the current user."""
    logger.info(f"Fetching notes for user: {current_user.username}, archived: {archived}")
    
    notes = db.query(Note).filter(
        Note.user_id == current_user.id,
        Note.is_archived == archived
    ).all()
    
    return notes

@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific note by ID."""
    logger.info(f"Fetching note ID: {note_id} for user: {current_user.username}")
    
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        logger.warning(f"Note not found or not owned by user: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to view it"
        )
    
    return note

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a note."""
    logger.info(f"Deleting note ID: {note_id} for user: {current_user.username}")
    
    note = db.query(Note).filter(
        Note.id == note_id,
        Note.user_id == current_user.id
    ).first()
    
    if not note:
        logger.warning(f"Note not found or not owned by user: {note_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found or you don't have permission to delete it"
        )
    
    db.delete(note)
    db.commit()
    
    logger.info(f"Note deleted successfully: {note_id}")
    return 