from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class PrescriptionCreate(BaseModel):
    patient_id: int
    diagnosis: str
    medicines: str
    instructions: Optional[str] = None

class PrescriptionUpdate(BaseModel):
    diagnosis: Optional[str] = None
    medicines: Optional[str] = None
    instructions: Optional[str] = None

class PrescriptionOut(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    diagnosis: str
    medicines: str
    instructions: Optional[str]
    created_at: datetime
    updated_at: datetime
    doctor_name: Optional[str] = None
    patient_name: Optional[str] = None
    class Config:
        from_attributes = True