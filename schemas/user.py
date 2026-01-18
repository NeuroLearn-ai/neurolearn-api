from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str | None = None
    avatar_url: str | None = None
    provider: str
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None
    avatar_url: str | None = None

    class Config:
        from_attributes = True