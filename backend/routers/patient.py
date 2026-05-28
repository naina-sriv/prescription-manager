from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import User
from auth import get_current_user

router = APIRouter(prefix="/patients", tags=["Patients"])

@router.get("")
def get_patients(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Doctors only")
    
    query = db.query(User).filter(User.role == "patient")
    if search:
        query = query.filter(User.name.ilike(f"%{search}%"))
    
    patients = query.all()
    return [{"id": p.id, "name": p.name, "email": p.email} for p in patients]

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }