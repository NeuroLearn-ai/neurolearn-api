from fastapi import APIRouter, Depends
from database import get_db
from sqlalchemy.ext.asyncio import AsyncSession

import models
import schemas
from security import get_current_user

router = APIRouter(
    prefix="/user",
    tags=["User"],
    responses={404: {"description": "Not found"}},
)

@router.get("/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=schemas.UserResponse)
async def update_user_me(
    user_update: schemas.UserUpdate, 
    current_user: models.User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    print("current_user:", current_user.email)
    
    if user_update.email:
        print("Updating email to:", user_update.email)
        current_user.email = user_update.email
        
    if user_update.name:
        print("Updating name to:", user_update.name)
        current_user.name = user_update.name 
        
    if user_update.avatar_url:
        print("Updating avatar to:", user_update.avatar_url)
        current_user.avatar_url = user_update.avatar_url

    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    
    return current_user