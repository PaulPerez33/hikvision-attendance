# app/routers/teacher_notes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db import SessionLocal
from app import models
from datetime import datetime

router = APIRouter(prefix="/notes", tags=["teacher_notes"])

# Pydantic schemas
class NoteCreate(BaseModel):
    student_id: int
    teacher_id: int
    note: str
    category: str | None = None  # "academico", "social", "deportivo", "artistico"

class NoteOut(BaseModel):
    id: int
    student_id: int
    teacher_id: int
    note: str
    category: str | None
    timestamp: datetime

    class Config:
        orm_mode = True

class NoteWithDetails(BaseModel):
    id: int
    note: str
    category: str | None
    timestamp: datetime
    student_name: str
    teacher_name: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=NoteOut)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    """Crear una nueva nota sobre un estudiante"""
    # Verificar que el estudiante existe
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar que el maestro existe
    teacher = db.query(models.User).filter(models.User.id == payload.teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="Maestro no encontrado")
    
    note = models.TeacherNote(
        student_id=payload.student_id,
        teacher_id=payload.teacher_id,
        note=payload.note,
        category=payload.category
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

@router.get("/student/{student_id}", response_model=list[NoteOut])
def get_student_notes(student_id: int, db: Session = Depends(get_db)):
    """Obtener todas las notas de un estudiante específico"""
    notes = db.query(models.TeacherNote).filter(
        models.TeacherNote.student_id == student_id
    ).order_by(models.TeacherNote.timestamp.desc()).all()
    return notes

@router.get("/", response_model=list[NoteWithDetails])
def list_all_notes(db: Session = Depends(get_db)):
    """Listar todas las notas con detalles de estudiante y maestro"""
    notes = db.query(
        models.TeacherNote,
        models.Student,
        models.User
    ).join(
        models.Student, models.TeacherNote.student_id == models.Student.id
    ).join(
        models.User, models.TeacherNote.teacher_id == models.User.id
    ).all()
    
    result = []
    for note, student, teacher in notes:
        result.append(NoteWithDetails(
            id=note.id,
            note=note.note,
            category=note.category,
            timestamp=note.timestamp,
            student_name=f"{student.first_name} {student.last_name}",
            teacher_name=teacher.full_name
        ))
    
    return result