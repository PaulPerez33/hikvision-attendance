# app/routers/dashboard.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, distinct
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from typing import List
from app.db import SessionLocal
from app import models
from app.auth import get_current_admin_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Schemas
class DashboardOverview(BaseModel):
    total_students: int
    total_teachers: int
    today_present: int
    today_absent: int
    today_attendance_rate: float
    week_attendance_rate: float
    total_notes: int

class AttendanceTrend(BaseModel):
    date: str
    present_count: int
    absent_count: int
    attendance_rate: float

class TopStudent(BaseModel):
    student_id: int
    student_name: str
    attendance_rate: float
    total_attendances: int

class StudentWithNotes(BaseModel):
    student_id: int
    student_name: str
    grade_level: str | None
    total_notes: int
    recent_note: str | None
    note_date: datetime | None

class TeacherActivity(BaseModel):
    teacher_id: int
    teacher_name: str
    total_notes: int
    last_activity: datetime | None

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/overview", response_model=DashboardOverview)
def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Vista general del dashboard para la directora.
    Requiere permisos de admin.
    """
    # Total de estudiantes
    total_students = db.query(models.Student).count()
    
    # Total de maestros
    total_teachers = db.query(models.User).filter(models.User.role == "teacher").count()
    
    # Asistencia de hoy
    today = date.today()
    today_present = db.query(func.count(distinct(models.Attendance.student_id))).filter(
        func.date(models.Attendance.timestamp) == today
    ).scalar() or 0
    
    today_absent = total_students - today_present
    today_rate = (today_present / total_students * 100) if total_students > 0 else 0
    
    # Asistencia promedio de la semana
    week_ago = today - timedelta(days=7)
    week_attendances = db.query(
        func.date(models.Attendance.timestamp).label('date'),
        func.count(distinct(models.Attendance.student_id)).label('count')
    ).filter(
        func.date(models.Attendance.timestamp) >= week_ago
    ).group_by(func.date(models.Attendance.timestamp)).all()
    
    if week_attendances and total_students > 0:
        week_avg = sum(att.count for att in week_attendances) / len(week_attendances)
        week_rate = (week_avg / total_students * 100)
    else:
        week_rate = 0
    
    # Total de notas de maestros
    total_notes = db.query(models.TeacherNote).count()
    
    return DashboardOverview(
        total_students=total_students,
        total_teachers=total_teachers,
        today_present=today_present,
        today_absent=today_absent,
        today_attendance_rate=round(today_rate, 2),
        week_attendance_rate=round(week_rate, 2),
        total_notes=total_notes
    )

@router.get("/attendance-trend", response_model=List[AttendanceTrend])
def get_attendance_trend(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Obtener tendencia de asistencia de los últimos N días.
    Por defecto 30 días.
    """
    total_students = db.query(models.Student).count()
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    
    trends = []
    current_date = start_date
    
    while current_date <= end_date:
        present_count = db.query(func.count(distinct(models.Attendance.student_id))).filter(
            func.date(models.Attendance.timestamp) == current_date
        ).scalar() or 0
        
        absent_count = total_students - present_count
        attendance_rate = (present_count / total_students * 100) if total_students > 0 else 0
        
        trends.append(AttendanceTrend(
            date=str(current_date),
            present_count=present_count,
            absent_count=absent_count,
            attendance_rate=round(attendance_rate, 2)
        ))
        
        current_date += timedelta(days=1)
    
    return trends

@router.get("/top-students", response_model=List[TopStudent])
def get_top_students(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Obtener los estudiantes con mejor asistencia.
    """
    # Obtener todos los estudiantes con su conteo de asistencias
    students_with_attendance = db.query(
        models.Student.id,
        models.Student.first_name,
        models.Student.last_name,
        func.count(distinct(func.date(models.Attendance.timestamp))).label('attendance_days')
    ).outerjoin(
        models.Attendance, models.Student.id == models.Attendance.student_id
    ).group_by(
        models.Student.id, models.Student.first_name, models.Student.last_name
    ).all()
    
    # Calcular días totales desde el primer registro de cada estudiante
    result = []
    for student in students_with_attendance:
        first_attendance = db.query(func.min(models.Attendance.timestamp)).filter(
            models.Attendance.student_id == student.id
        ).scalar()
        
        if first_attendance:
            total_days = (date.today() - first_attendance.date()).days + 1
            attendance_rate = (student.attendance_days / total_days * 100) if total_days > 0 else 0
        else:
            attendance_rate = 0
        
        result.append(TopStudent(
            student_id=student.id,
            student_name=f"{student.first_name} {student.last_name}",
            attendance_rate=round(attendance_rate, 2),
            total_attendances=student.attendance_days
        ))
    
    # Ordenar por tasa de asistencia y limitar
    result.sort(key=lambda x: x.attendance_rate, reverse=True)
    return result[:limit]

@router.get("/students-with-notes", response_model=List[StudentWithNotes])
def get_students_with_notes(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Obtener estudiantes con notas de maestros para seguimiento.
    """
    students = db.query(models.Student).all()
    
    result = []
    for student in students:
        notes = db.query(models.TeacherNote).filter(
            models.TeacherNote.student_id == student.id
        ).order_by(models.TeacherNote.timestamp.desc()).all()
        
        if notes:
            result.append(StudentWithNotes(
                student_id=student.id,
                student_name=f"{student.first_name} {student.last_name}",
                grade_level=student.grade_level,
                total_notes=len(notes),
                recent_note=notes[0].note,
                note_date=notes[0].timestamp
            ))
    
    # Ordenar por cantidad de notas (descendente)
    result.sort(key=lambda x: x.total_notes, reverse=True)
    return result

@router.get("/teacher-activity", response_model=List[TeacherActivity])
def get_teacher_activity(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Obtener actividad de maestros (cuántas notas han registrado).
    """
    teachers = db.query(models.User).filter(models.User.role == "teacher").all()
    
    result = []
    for teacher in teachers:
        notes = db.query(models.TeacherNote).filter(
            models.TeacherNote.teacher_id == teacher.id
        ).order_by(models.TeacherNote.timestamp.desc()).all()
        
        result.append(TeacherActivity(
            teacher_id=teacher.id,
            teacher_name=teacher.full_name,
            total_notes=len(notes),
            last_activity=notes[0].timestamp if notes else None
        ))
    
    # Ordenar por actividad (descendente)
    result.sort(key=lambda x: x.total_notes, reverse=True)
    return result

@router.get("/absent-students-today")
def get_absent_students_today(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Obtener lista de estudiantes ausentes hoy.
    """
    today = date.today()
    
    # Estudiantes que asistieron hoy
    present_ids = db.query(models.Attendance.student_id).filter(
        func.date(models.Attendance.timestamp) == today
    ).distinct().all()
    
    present_ids_list = [pid[0] for pid in present_ids]
    
    # Estudiantes ausentes
    absent_students = db.query(models.Student).filter(
        ~models.Student.id.in_(present_ids_list)
    ).all()
    
    return [
        {
            "id": student.id,
            "name": f"{student.first_name} {student.last_name}",
            "grade_level": student.grade_level,
            "photo_path": student.photo_path
        }
        for student in absent_students
    ]

@router.get("/monthly-report")
def get_monthly_report(
    year: int,
    month: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin_user)
):
    """
    Obtener reporte mensual de asistencias.
    """
    # Validar mes
    if month < 1 or month > 12:
        raise HTTPException(status_code=400, detail="Mes inválido (1-12)")
    
    # Calcular fechas del mes
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
    
    total_students = db.query(models.Student).count()
    
    # Asistencias por día del mes
    daily_stats = []
    current_date = start_date
    
    while current_date <= end_date:
        present_count = db.query(func.count(distinct(models.Attendance.student_id))).filter(
            func.date(models.Attendance.timestamp) == current_date
        ).scalar() or 0
        
        daily_stats.append({
            "date": str(current_date),
            "day_of_week": current_date.strftime("%A"),
            "present": present_count,
            "absent": total_students - present_count,
            "rate": round((present_count / total_students * 100), 2) if total_students > 0 else 0
        })
        
        current_date += timedelta(days=1)
    
    # Estadísticas generales del mes
    total_possible_attendances = total_students * len(daily_stats)
    total_attendances = sum(day["present"] for day in daily_stats)
    monthly_rate = (total_attendances / total_possible_attendances * 100) if total_possible_attendances > 0 else 0
    
    return {
        "year": year,
        "month": month,
        "month_name": start_date.strftime("%B"),
        "total_students": total_students,
        "total_school_days": len(daily_stats),
        "monthly_attendance_rate": round(monthly_rate, 2),
        "daily_stats": daily_stats
    }
