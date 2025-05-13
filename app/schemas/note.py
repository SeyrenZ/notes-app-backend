from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime

# Tag schemas
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int

    class Config:
        from_attributes = True

# Note schemas
class NoteBase(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_archived: Optional[bool] = False
    theme_color: Optional[str] = None
    font_family: Optional[str] = None

class NoteCreate(NoteBase):
    pass

class NoteUpdate(NoteBase):
    pass

class NoteResponse(NoteBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    tags: List[TagResponse] = []

    class Config:
        from_attributes = True

# For adding tags to notes
class NoteTagLink(BaseModel):
    note_id: int
    tag_id: int 