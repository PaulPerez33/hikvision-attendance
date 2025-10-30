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
    student = models.Student(first_name=payload.first_name, last_name=payload.last_name, photo_path=payload.photo_path)
    db.add(student)
    db.commit()
    db.refresh(student)
    return student

@router.get("/", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.query(models.Student).all()
