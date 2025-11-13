from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True)
    full_name = Column(String(256))
    role = Column(String(50))  # admin, teacher
    hashed_password = Column(String(256))  # Para autenticación futura

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(128))
    last_name = Column(String(128))
    photo_path = Column(String(256), nullable=True)
    grade_level = Column(String(50), nullable=True)  # "primaria", "secundaria", "preparatoria"
    
    # Relaciones
    attendances = relationship("Attendance", back_populates="student")
    teacher_notes = relationship("TeacherNote", back_populates="student")

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    camera_id = Column(String(64))
    matched = Column(Boolean, default=True)
    
    # Relación
    student = relationship("Student", back_populates="attendances")

class TeacherNote(Base):
    __tablename__ = "teacher_notes"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    teacher_id = Column(Integer, ForeignKey("users.id"))
    note = Column(Text)  # El comentario del maestro
    category = Column(String(100), nullable=True)  # "academico", "social", "deportivo", "artistico"
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relaciones
    student = relationship("Student", back_populates="teacher_notes")
    teacher = relationship("User")