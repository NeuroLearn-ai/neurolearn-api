from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, Form
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pdf2image import convert_from_bytes
from database import get_db
import uuid
import os
from security import get_current_user

import models
import schemas

upload_dir = os.getenv("UPLOAD_DIRECTORY", "static/uploads")

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    responses={404: {"description": "Not found"}},
)

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
    back_type: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    note = models.Note(
        title=title,
        owner_id=current_user.id,
        pages=[]
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)
    
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
                overlay_data=None
            )
            db.add(page)
        
        await db.commit()
        await db.refresh(note)
    else:
        page = models.Page(
            note_id=note.id,
            page_number=1,
            content="",
            background_type=back_type if back_type else "plain",
            background_url=None,
            overlay_data=None
        )
        db.add(page)
        note.pages.append(page)
        
        await db.commit()
        await db.refresh(note)
    
    result = await db.execute(
        select(models.Note)
        .where(models.Note.id == note.id)
        .options(selectinload(models.Note.pages))
    )
    created_note = result.scalars().first()
    return created_note