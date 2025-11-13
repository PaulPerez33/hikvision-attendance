# app/routers/attendance.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from app.db import SessionLocal
from app import models
from app.auth import get_current_user
import xml.etree.ElementTree as ET

router = APIRouter(prefix="/attendance", tags=["attendance"])

# Schemas
class AttendanceOut(BaseModel):
    id: int
    student_id: int
    timestamp: datetime
    camera_id: str
    matched: bool
    student_name: str | None = None

    class Config:
        from_attributes = True

class AttendanceStats(BaseModel):
    date: str
    total_students: int
    present_count: int
    absent_count: int
    attendance_rate: float

class StudentAttendanceHistory(BaseModel):
    student_id: int
    student_name: str
    total_days: int
    present_days: int
    absent_days: int
    attendance_rate: float
    last_attendance: datetime | None

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/webhook")
async def camera_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Webhook para recibir eventos de reconocimiento facial de la cámara Hikvision.
    La cámara envía XML cuando detecta un rostro.
    """
    try:
        # Leer el body XML enviado por la cámara
        body = await request.body()
        
        # Log del evento recibido
        print(f"[Webhook] Evento recibido de la cámara:")
        print(body.decode('utf-8'))
        
        # Parsear XML
        root = ET.fromstring(body)
        
        # Extraer información del evento
        # Estos campos varían según el modelo de cámara, ajusta según tu documentación
        person_id = root.find('.//employeeNo')  # ID del rostro en la biblioteca
        match_score = root.find('.//similarityScore')  # Puntuación de coincidencia
        capture_time = root.find('.//dateTime')  # Timestamp del evento
        
        if person_id is not None:
            student_id = int(person_id.text)
            confidence = float(match_score.text) if match_score is not None else 0.0
            
            # Verificar que el estudiante existe
            student = db.query(models.Student).filter(models.Student.id == student_id).first()
            
            if student:
                # Crear registro de asistencia
                attendance = models.Attendance(
                    student_id=student_id,
                    camera_id=request.client.host,
                    matched=confidence > 0.75,  # Considerar matched si confianza > 75%
                    timestamp=datetime.utcnow()
                )
                db.add(attendance)
                db.commit()
                
                print(f"[Webhook] Asistencia registrada: {student.first_name} {student.last_name} - Confianza: {confidence}")
                
                return {
                    "status": "success",
                    "message": "Asistencia registrada",
                    "student": {
                        "id": student.id,
                        "name": f"{student.first_name} {student.last_name}"
                    },
                    "confidence": confidence
                }
            else:
                print(f"[Webhook] Estudiante no encontrado: ID {student_id}")
                return {"status": "error", "message": "Estudiante no encontrado"}
        
        return {"status": "error", "message": "No se pudo extraer información del evento"}
        
    except Exception as e:
        print(f"[Webhook] Error procesando evento: {str(e)}")
        return {"status": "error", "message": str(e)}

@router.post("/manual")
def register_manual_attendance(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Registrar asistencia manualmente (para casos especiales)"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    attendance = models.Attendance(
        student_id=student_id,
        camera_id="manual",
        matched=True,
        timestamp=datetime.utcnow()
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return {
        "status": "success",
        "message": f"Asistencia registrada para {student.first_name} {student.last_name}",
        "attendance": attendance
    }

@router.get("/today", response_model=list[AttendanceOut])
def get_today_attendance(db: Session = Depends(get_db)):
    """Obtener todas las asistencias del día de hoy"""
    today = date.today()
    attendances = db.query(
        models.Attendance,
        models.Student
    ).join(
        models.Student, models.Attendance.student_id == models.Student.id
    ).filter(
        func.date(models.Attendance.timestamp) == today
    ).all()
    
    result = []
    for attendance, student in attendances:
        result.append(AttendanceOut(
            id=attendance.id,
            student_id=attendance.student_id,
            timestamp=attendance.timestamp,
            camera_id=attendance.camera_id,
            matched=attendance.matched,
            student_name=f"{student.first_name} {student.last_name}"
        ))
    
    return result

@router.get("/student/{student_id}")
def get_student_attendance_history(student_id: int, db: Session = Depends(get_db)):
    """Obtener historial de asistencias de un estudiante"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    attendances = db.query(models.Attendance).filter(
        models.Attendance.student_id == student_id
    ).order_by(models.Attendance.timestamp.desc()).all()
    
    # Calcular días únicos de asistencia
    unique_dates = set()
    for att in attendances:
        unique_dates.add(att.timestamp.date())
    
    present_days = len(unique_dates)
    
    # Calcular días totales (desde la primera asistencia hasta hoy)
    if attendances:
        first_date = min(att.timestamp.date() for att in attendances)
        total_days = (date.today() - first_date).days + 1
    else:
        total_days = 0
    
    absent_days = max(0, total_days - present_days)
    attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
    
    return StudentAttendanceHistory(
        student_id=student.id,
        student_name=f"{student.first_name} {student.last_name}",
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        attendance_rate=round(attendance_rate, 2),
        last_attendance=attendances[0].timestamp if attendances else None
    )

@router.get("/stats/today")
def get_today_stats(db: Session = Depends(get_db)):
    """Obtener estadísticas de asistencia del día"""
    today = date.today()
    
    # Total de estudiantes
    total_students = db.query(models.Student).count()
    
    # Estudiantes que asistieron hoy (contar IDs únicos)
    present_today = db.query(func.count(func.distinct(models.Attendance.student_id))).filter(
        func.date(models.Attendance.timestamp) == today
    ).scalar()
    
    absent_today = total_students - present_today
    attendance_rate = (present_today / total_students * 100) if total_students > 0 else 0
    
    return AttendanceStats(
        date=str(today),
        total_students=total_students,
        present_count=present_today,
        absent_count=absent_today,
        attendance_rate=round(attendance_rate, 2)
    )

@router.get("/stats/range")
def get_stats_by_date_range(
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db)
):
    """Obtener estadísticas de asistencia en un rango de fechas"""
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido. Usar YYYY-MM-DD")
    
    total_students = db.query(models.Student).count()
    
    stats = []
    current_date = start
    while current_date <= end:
        present_count = db.query(func.count(func.distinct(models.Attendance.student_id))).filter(
            func.date(models.Attendance.timestamp) == current_date
        ).scalar()
        
        absent_count = total_students - present_count
        attendance_rate = (present_count / total_students * 100) if total_students > 0 else 0
        
        stats.append(AttendanceStats(
            date=str(current_date),
            total_students=total_students,
            present_count=present_count,
            absent_count=absent_count,
            attendance_rate=round(attendance_rate, 2)
        ))
        
        current_date += timedelta(days=1)
    
    return stats
