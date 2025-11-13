# app/routers/students.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import SessionLocal
from app import models

router = APIRouter(prefix="/students", tags=["students"])

# Pydantic schemas
class StudentCreate(BaseModel):
    first_name: str
    last_name: str
    photo_path: str | None = None

class StudentUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    photo_path: str | None = None

class StudentOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    photo_path: str | None = None

    class Config:
        orm_mode = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=StudentOut)
def create_student(payload: StudentCreate, db: Session = Depends(get_db)):
    """Crear un nuevo estudiante"""
    student = models.Student(
        first_name=payload.first_name, 
        last_name=payload.last_name, 
        photo_path=payload.photo_path
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@router.get("/", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    """Listar todos los estudiantes"""
    return db.query(models.Student).all()

@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Obtener un estudiante específico por ID"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    return student

@router.put("/{student_id}", response_model=StudentOut)
def update_student(student_id: int, payload: StudentUpdate, db: Session = Depends(get_db)):
    """Actualizar información de un estudiante"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Actualizar solo los campos que se enviaron
    if payload.first_name is not None:
        student.first_name = payload.first_name
    if payload.last_name is not None:
        student.last_name = payload.last_name
    if payload.photo_path is not None:
        student.photo_path = payload.photo_path
    
    db.commit()
    db.refresh(student)
    return student

@router.delete("/{student_id}")
def delete_student(student_id: int, db: Session = Depends(get_db)):
    """Eliminar un estudiante"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    db.delete(student)
    db.commit()
    return {"message": "Estudiante eliminado correctamente", "id": student_id}