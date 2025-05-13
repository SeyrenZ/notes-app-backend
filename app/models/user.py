from sqlalchemy import Boolean, Column, Integer, String, Text
from app.db.session import engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    is_active = Column(Boolean, default=True)
    
    # OAuth related fields
    google_id = Column(String(255), unique=True, nullable=True, index=True)
    profile_picture = Column(String(512), nullable=True)
    
    # Relationship with notes
    notes = relationship("Note", back_populates="user", cascade="all, delete-orphan")

# Create tables
Base.metadata.create_all(bind=engine) 