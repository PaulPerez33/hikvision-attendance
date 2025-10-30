from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.db import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True)
    full_name = Column(String(256))
    role = Column(String(50))  # admin, teacher

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(128))
    last_name = Column(String(128))
    photo_path = Column(String(256), nullable=True)

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    camera_id = Column(String(64))
    matched = Column(Boolean, default=True)
