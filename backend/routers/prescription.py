from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import User, Prescription
from schema import PrescriptionCreate, PrescriptionUpdate, PrescriptionOut
from auth import get_current_user
from pdf_gen import generate_prescription_pdf
from ocr import process_prescription_image

router = APIRouter(prefix="/prescriptions", tags=["Prescriptions"])

@router.post("", response_model=PrescriptionOut)
def create_prescription(
    data: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can create prescriptions")
    
    patient = db.query(User).filter(
        User.id == data.patient_id,
        User.role == "patient"
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    prescription = Prescription(**data.dict(), doctor_id=current_user.id)
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    
    out = PrescriptionOut.from_orm(prescription)
    out.doctor_name = current_user.name
    out.patient_name = patient.name
    return out

@router.get("", response_model=List[PrescriptionOut])
def get_prescriptions(
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "patient":
        query = db.query(Prescription).filter(Prescription.patient_id == current_user.id)
    else:
        query = db.query(Prescription).filter(Prescription.doctor_id == current_user.id)
    
    if search:
        query = query.filter(Prescription.diagnosis.ilike(f"%{search}%"))
    
    prescriptions = query.order_by(Prescription.created_at.desc()).all()

    results = []
    for p in prescriptions:
        out = PrescriptionOut.from_orm(p)
        out.doctor_name = p.doctor.name if p.doctor else "Unknown"
        out.patient_name = p.patient.name if p.patient else "Unknown"
        results.append(out)
    return results

@router.put("/{id}", response_model=PrescriptionOut)
def update_prescription(
    id: int,
    data: PrescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only doctors can update prescriptions")
    
    prescription = db.query(Prescription).filter(
        Prescription.id == id,
        Prescription.doctor_id == current_user.id
    ).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Prescription not found")
    
    for field, value in data.dict(exclude_unset=True).items():
        setattr(prescription, field, value)
    
    db.commit()
    db.refresh(prescription)
    
    out = PrescriptionOut.from_orm(prescription)
    out.doctor_name = prescription.doctor.name
    out.patient_name = prescription.patient.name
    return out

@router.get("/{id}/pdf")
def download_pdf(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescription = db.query(Prescription).filter(Prescription.id == id).first()
    if not prescription:
        raise HTTPException(status_code=404, detail="Not found")
    if current_user.role == "patient" and prescription.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    pdf = generate_prescription_pdf(
        prescription,
        prescription.doctor.name,
        prescription.patient.name
    )
    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=prescription_{id}.pdf"}
    )

@router.post("/scanned")
def save_scanned_prescription(
    data: PrescriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prescription = Prescription(
        patient_id=current_user.id,
        doctor_id=current_user.id,
        diagnosis=data.diagnosis,
        medicines=data.medicines,
        instructions=data.instructions or "Scanned from paper prescription"
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)
    return {"message": "Saved", "id": prescription.id}

@router.post("/ocr")
async def ocr_prescription(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(status_code=400, detail="Only image files accepted (jpg, png, webp)")
    
    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large, max 10MB")
    
    try:
        result = process_prescription_image(image_bytes)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))