# app/routers/camera.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.hikvision import get_hikvision_client
from app.db import SessionLocal
from app import models

router = APIRouter(prefix="/camera", tags=["camera"])

class CameraTestResponse(BaseModel):
    status: str
    message: str
    device_info: dict | None = None

class EnrollFaceRequest(BaseModel):
    student_id: int
    library_id: str = "school_library"

class DetectionEvent(BaseModel):
    student_id: int
    confidence: float
    timestamp: str
    camera_id: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/test", response_model=CameraTestResponse)
def test_camera_connection():
    """Probar conexión con la cámara Hikvision"""
    client = get_hikvision_client()
    result = client.test_connection()
    
    return CameraTestResponse(
        status=result["status"],
        message=result["message"],
        device_info=result.get("device_info")
    )

@router.post("/library/create")
def create_face_library(library_id: str = "school_library", library_name: str = "Escuela Principal"):
    """Crear biblioteca de rostros en la cámara"""
    client = get_hikvision_client()
    result = client.create_face_library(library_id, library_name)
    return result

@router.post("/enroll")
def enroll_student_face(payload: EnrollFaceRequest, db: Session = Depends(get_db)):
    """Enrollar el rostro de un estudiante en la cámara"""
    # Verificar que el estudiante existe
    student = db.query(models.Student).filter(models.Student.id == payload.student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    # Verificar que tiene foto
    if not student.photo_path:
        raise HTTPException(status_code=400, detail="El estudiante no tiene foto registrada")
    
    # Enrollar en la cámara
    client = get_hikvision_client()
    full_name = f"{student.first_name} {student.last_name}"
    
    result = client.enroll_face(
        library_id=payload.library_id,
        person_id=str(student.id),
        person_name=full_name,
        image_path=student.photo_path
    )
    
    return {
        "student": {
            "id": student.id,
            "name": full_name
        },
        "enrollment": result
    }

@router.delete("/enroll/{student_id}")
def delete_student_face(student_id: int, library_id: str = "school_library", db: Session = Depends(get_db)):
    """Eliminar rostro de un estudiante de la cámara"""
    student = db.query(models.Student).filter(models.Student.id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Estudiante no encontrado")
    
    client = get_hikvision_client()
    result = client.delete_face(library_id, str(student_id))
    
    return result

@router.get("/events")
def get_detection_events():
    """Obtener eventos de detección facial de la cámara"""
    client = get_hikvision_client()
    result = client.get_face_detection_events()
    return result

@router.get("/snapshot")
def get_camera_snapshot():
    """Obtener una captura de imagen de la cámara"""
    client = get_hikvision_client()
    result = client.get_snapshot()
    
    if result["status"] == "success":
        import base64
        img_base64 = base64.b64encode(result["image_data"]).decode('utf-8')
        return {
            "status": "success",
            "image": f"data:image/jpeg;base64,{img_base64}"
        }
    else:
        raise HTTPException(status_code=500, detail=result["message"])