from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pdf2image import convert_from_bytes
from database import get_db
import uuid
import os
from security import get_current_user
from typing import Dict, Any

import models
import schemas

upload_dir = os.getenv("UPLOAD_DIRECTORY", "static/uploads")

class PageOverlayUpdate(BaseModel):
    overlay_data: Dict[str, Any]  # Stores JSON data (strokes, text, etc.)

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    responses={404: {"description": "Not found"}},
)

@router.get("", response_model=List[schemas.NoteResponse])
async def get_all_notes(
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    query = (
        select(models.Note)
        .where(models.Note.owner_id == current_user.id)
        .options(selectinload(models.Note.pages))
        .order_by(models.Note.created_at.desc())
    )
    result = await db.execute(query)
    notes = result.scalars().all()
    return notes


@router.get("/{note_id}", response_model=schemas.NoteResponse)
async def get_note(
    note_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # 1. Fetch Note with Pages loaded
    query = select(models.Note).where(models.Note.id == note_id).options(selectinload(models.Note.pages))
    result = await db.execute(query)
    note = result.scalars().first()

    # 2. Check if it exists
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # 3. Check ownership (Security)
    if note.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this note")
    
    return note


@router.post("", response_model=schemas.NoteResponse)
async def create_note(
    title: str = Form(...),
    back_type: Optional[str] = Form("plain"),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    note = models.Note(title=title, owner_id=current_user.id)
    db.add(note)
    await db.commit()
    stmt = select(models.Note).options(selectinload(models.Note.pages)).where(models.Note.id == note.id)
    result = await db.execute(stmt)
    note = result.scalars().first()
    
    try:
        if file:
            file_bytes = await file.read()
            images = convert_from_bytes(file_bytes)
            
            for i, image in enumerate(images):
                filename = f"note_{note.id}_{uuid.uuid4()}.png"
                filepath = os.path.join(upload_dir, filename)
                file_url = f"/static/uploads/{filename}"
                image.save(filepath, "PNG")
                
                page = models.Page(
                    note_id=note.id,
                    page_number=i + 1,
                    content="",
                    background_type="image",
                    background_url=file_url,
                    overlay_data={}
                )
                db.add(page)
        else:
            page = models.Page(
                note_id=note.id,
                page_number=1,
                content="",
                background_type=back_type or "plain",
                background_url=None,
                overlay_data={}
            )
            db.add(page)
            
        await db.commit()
        
    except Exception as e:
        await db.delete(note)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Server Error: {str(e)}")
    
    result = await db.execute(
        select(models.Note)
        .where(models.Note.id == note.id)
        .options(selectinload(models.Note.pages))
    )
    created_note = result.scalars().first()
    return created_note


@router.patch("/pages/{page_id}", response_model=schemas.PageResponse) # Ensure PageResponse is imported or defined
async def update_page_overlay(
    page_id: int,
    update_data: PageOverlayUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Fetch the page
    result = await db.execute(
        select(models.Page)
        .join(models.Note)
        .where(models.Page.id == page_id)
        .where(models.Note.owner_id == current_user.id)
    )
    page = result.scalars().first()

    if not page:
        raise HTTPException(status_code=404, detail="Page not found or unauthorized")

    # Update the JSONB column
    page.overlay_data = update_data.overlay_data
    
    await db.commit()
    await db.refresh(page)
    
    return page