from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class PageResponse(BaseModel):
    id: int
    page_number: int
    background_type: str
    background_url: Optional[str] = None
    overlay_data: Optional[dict] = None

    class Config:
        from_attributes = True

class NoteCreate(BaseModel):
    title: str
    category: Optional[str] = "plain" # For blank notes

class NoteResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    pages: List[PageResponse] = []

    class Config:
        from_attributes = True