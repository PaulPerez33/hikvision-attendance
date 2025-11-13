# app/routers/ai_analysis.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from app.db import SessionLocal
from app import models
from app.auth import get_current_user, get_current_teacher_or_admin
from app.ai_service import analyze_student_for_career, generate_student_report, batch_analyze_students

router = APIRouter(prefix="/ai", tags=["ai_analysis"])

# Schemas
class CareerSuggestion(BaseModel):
    career: str
    match_percentage: int
    reasoning: str
    related_skills: List[str]

class StudentAnalysis(BaseModel):
    student_id: int
    student_name: str
    status: str
    student_summary: str | None = None
    strengths: List[str] | None = None
    interests: List[str] | None = None
    career_suggestions: List[Dict[str, Any]] | None = None
    recommendations: str | None = None
    message: str | None = None

class BatchAnalysisRequest(BaseModel):
    student_ids: List[int]

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/analyze-student/{student_id}", response_model=StudentAnalysis)
def analyze_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_teacher_or_admin)
):
    """
    Analizar un estudiante específico y generar sugerencias de carrera
    basadas en las notas de los maestros.
    """
    # Obtener estudiante
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Obtener todas las notas del estudiante
    notes = db.query(models.TeacherNote).filter(
        models.TeacherNote.student_id == student_id
    ).order_by(models.TeacherNote.timestamp.desc()).all()
    
    # Preparar datos de notas para el análisis
    notes_data = [
        {
            "note": note.note,
            "category": note.category or "general",
            "date": note.timestamp.strftime("%Y-%m-%d")
        }
        for note in notes
    ]
    
    student_name = f"{student.first_name} {student.last_name}"
    
    # Llamar al servicio de IA
    analysis = analyze_student_for_career(student_name, notes_data)
    
    # Construir respuesta
    response = StudentAnalysis(
        student_id=student.id,
        student_name=student_name,
        status=analysis.get("status", "unknown"),
        student_summary=analysis.get("student_summary"),
        strengths=analysis.get("strengths"),
        interests=analysis.get("interests"),
        career_suggestions=analysis.get("career_suggestions"),
        recommendations=analysis.get("recommendations"),
        message=analysis.get("message")
    )
    
    return response

@router.get("/student-report/{student_id}")
def get_student_report(
    student_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_teacher_or_admin)
):
    """
    Generar un reporte completo en texto del estudiante
    con análisis de carrera.
    """
    # Obtener estudiante
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Obtener notas
    notes = db.query(models.TeacherNote).filter(
        models.TeacherNote.student_id == student_id
    ).all()
    
    # Obtener asistencia
    from sqlalchemy import func, distinct
    from datetime import date
    
    attendance_count = db.query(func.count(distinct(func.date(models.Attendance.timestamp)))).filter(
        models.Attendance.student_id == student_id
    ).scalar() or 0
    
    first_attendance = db.query(func.min(models.Attendance.timestamp)).filter(
        models.Attendance.student_id == student_id
    ).scalar()
    
    if first_attendance:
        total_days = (date.today() - first_attendance.date()).days + 1
        attendance_rate = (attendance_count / total_days * 100) if total_days > 0 else 0
    else:
        attendance_rate = 0
    
    # Preparar datos
    notes_summary = "\n".join([
        f"- [{note.category}] {note.note} ({note.timestamp.strftime('%Y-%m-%d')})"
        for note in notes
    ])
    
    # Obtener análisis de carrera primero
    notes_data = [
        {
            "note": note.note,
            "category": note.category or "general",
            "date": note.timestamp.strftime("%Y-%m-%d")
        }
        for note in notes
    ]
    
    student_name = f"{student.first_name} {student.last_name}"
    career_analysis = analyze_student_for_career(student_name, notes_data)
    
    # Formatear análisis de carrera
    if career_analysis.get("status") == "success" and career_analysis.get("career_suggestions"):
        career_text = "\n".join([
            f"  {i+1}. {c['career']} (Compatibilidad: {c['match_percentage']}%)\n     Razón: {c['reasoning']}"
            for i, c in enumerate(career_analysis["career_suggestions"])
        ])
    else:
        career_text = "No hay suficientes datos para generar sugerencias de carrera"
    
    student_data = {
        "name": student_name,
        "grade_level": student.grade_level or "No especificado",
        "attendance_rate": round(attendance_rate, 2),
        "total_attendances": attendance_count,
        "notes_summary": notes_summary or "No hay observaciones registradas",
        "career_analysis": career_text
    }
    
    # Generar reporte
    report = generate_student_report(student_data)
    
    return {
        "student_id": student.id,
        "student_name": student_name,
        "report": report,
        "generated_at": date.today().isoformat()
    }

@router.post("/batch-analyze")
def batch_analyze(
    request: BatchAnalysisRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_teacher_or_admin)
):
    """
    Analizar múltiples estudiantes a la vez para identificar patrones
    y generar recomendaciones para la institución.
    """
    if not request.student_ids:
        raise HTTPException(status_code=400, detail="Se requiere al menos un student_id")
    
    students_data = []
    
    for student_id in request.student_ids:
        student = db.query(models.Student).filter(models.Student.id == student_id).first()
        if not student:
            continue
        
        # Obtener notas
        notes = db.query(models.TeacherNote).filter(
            models.TeacherNote.student_id == student_id
        ).limit(5).all()  # Solo las 5 más recientes para el análisis grupal
        
        key_notes = [note.note for note in notes]
        
        students_data.append({
            "name": f"{student.first_name} {student.last_name}",
            "grade_level": student.grade_level or "N/A",
            "key_notes": key_notes
        })
    
    if not students_data:
        raise HTTPException(status_code=404, detail="No se encontraron estudiantes con los IDs proporcionados")
    
    # Analizar grupo
    analysis = batch_analyze_students(students_data)
    
    return analysis

@router.get("/test-connection")
def test_ai_connection(current_user: models.User = Depends(get_current_user)):
    """
    Probar la conexión con la API de Google Gemini.
    """
    try:
        import google.generativeai as genai
        import os
        
        api_key = os.getenv("GEMINI_API_KEY", "")
        genai.configure(api_key=api_key)
        
        # Listar modelos disponibles
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        
        # Probar con el primer modelo disponible
        if available_models:
            model_name = available_models[0].replace('models/', '')
            model = genai.GenerativeModel(model_name)
            response = model.generate_content("Responde con 'Conexión exitosa'")
            
            return {
                "status": "success",
                "message": "Conexión con Gemini API exitosa",
                "model_used": model_name,
                "available_models": available_models,
                "response": response.text
            }
        else:
            return {
                "status": "error",
                "message": "No hay modelos disponibles"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error: {str(e)}"
        }