from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str  # "doctor" or "patient"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

