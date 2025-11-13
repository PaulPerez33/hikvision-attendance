# app/routers/stream.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import requests
from requests.auth import HTTPDigestAuth
import os

router = APIRouter(prefix="/stream", tags=["stream"])

def get_camera_credentials():
    """Obtener credenciales de la cámara"""
    return {
        "ip": os.getenv("HIKVISION_IP", "192.168.100.13"),
        "username": os.getenv("HIKVISION_USER", "admin"),
        "password": os.getenv("HIKVISION_PASSWORD", "Lenovob490!")
    }

@router.get("/live")
async def stream_camera():
    """
    Proxy para el stream de video de la cámara Hikvision.
    Maneja la autenticación y transmite el video al frontend.
    """
    creds = get_camera_credentials()
    stream_url = f"http://{creds['ip']}/ISAPI/Streaming/channels/101/httpPreview"
    
    try:
        # Hacer request con autenticación
        response = requests.get(
            stream_url,
            auth=HTTPDigestAuth(creds['username'], creds['password']),
            stream=True,
            timeout=10
        )
        
        # Stream generator
        def generate():
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk
        
        return StreamingResponse(
            generate(),
            media_type="multipart/x-mixed-replace; boundary=--myboundary"
        )
    
    except Exception as e:
        print(f"Error en stream: {str(e)}")
        return {"error": str(e)}

@router.get("/snapshot")
async def get_snapshot():
    """Obtener una captura estática de la cámara"""
    creds = get_camera_credentials()
    snapshot_url = f"http://{creds['ip']}/ISAPI/Streaming/channels/1/picture"
    
    try:
        response = requests.get(
            snapshot_url,
            auth=HTTPDigestAuth(creds['username'], creds['password']),
            timeout=5
        )
        
        if response.status_code == 200:
            return StreamingResponse(
                iter([response.content]),
                media_type="image/jpeg"
            )
        else:
            return {"error": f"Error {response.status_code}"}
    
    except Exception as e:
        return {"error": str(e)}