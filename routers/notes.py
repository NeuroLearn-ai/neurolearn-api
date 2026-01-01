from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

import models
import schemas
from database import get_db

router = APIRouter(
    prefix="/notes",
    tags=["Notes"],
    responses={404: {"description": "Not found"}},
)

@router.get("/notes/", response_model=list[schemas.NoteResponse])
async def read_notes(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Note))
    notes = result.scalars().all()
    return notes

@router.get("/notes/{note_id}", response_model=schemas.NoteResponse)
async def read_note(note_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Note).where(models.Note.id == note_id))
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note

@router.post("/notes/", response_model=schemas.NoteResponse)
async def create_note(note: schemas.NoteCreate, db: AsyncSession = Depends(get_db)):
    new_note = models.Note(title=note.title, content=note.content)
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note