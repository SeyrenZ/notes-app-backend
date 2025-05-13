from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import engine

from app.models.user import Base, User

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    content = Column(Text)
    is_archived = Column(Boolean, default=False)
    theme_color = Column(String(20))
    font_family = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship with user
    user = relationship("User", back_populates="notes")
    # Relationship with tags through note_tags
    tags = relationship("Tag", secondary="note_tags", back_populates="notes")


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

    # Relationship with notes through note_tags
    notes = relationship("Note", secondary="note_tags", back_populates="tags")


# Association table for many-to-many relationship between notes and tags
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

# Create tables
Base.metadata.create_all(bind=engine) 