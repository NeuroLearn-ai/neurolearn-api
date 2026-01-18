from database import Base
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    pages = relationship("Page", back_populates="note", order_by="Page.page_number")

class Page(Base):
    __tablename__ = "pages"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"))
    page_number = Column(Integer, index=True)
    content = Column(Text)
    
    background_type = Column(String, default="plain")  # image, plain, ruled, grid
    background_url = Column(String, nullable=True)     # URL for image background
    overlay_data = Column(JSONB, nullable=True)        # JSON data for overlays like highlights, drawings, etc.

    note = relationship("Note", back_populates="pages")