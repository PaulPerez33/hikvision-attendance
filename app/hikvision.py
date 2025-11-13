# app/hikvision.py
import requests
from requests.auth import HTTPDigestAuth
import xml.etree.ElementTree as ET
import base64
import os
import urllib3

# Deshabilitar warnings de SSL para desarrollo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class HikvisionClient:
    def __init__(self, camera_ip: str, username: str, password: str, use_https: bool = False):
        self.camera_ip = camera_ip
        self.username = username
        self.password = password
        self.use_https = use_https
        
        # Construir URL base
        protocol = "https" if use_https else "http"
        self.base_url = f"{protocol}://{camera_ip}/ISAPI"
        
        self.auth = HTTPDigestAuth(username, password)
        print(f"[Hikvision] Cliente inicializado: {self.base_url}")
    
    def test_connection(self):
        """Probar conexión con la cámara"""
        try:
            url = f"{self.base_url}/System/deviceInfo"
            print(f"[Hikvision] Probando conexión a: {url}")
            response = requests.get(url, auth=self.auth, timeout=10, verify=False)
            
            if response.status_code == 200:
                # Parsear información del dispositivo
                try:
                    root = ET.fromstring(response.content)
                    device_name = root.find('.//deviceName')
                    model = root.find('.//model')
                    serial = root.find('.//serialNumber')
                    firmware = root.find('.//firmwareVersion')
                    
                    return {
                        "status": "success", 
                        "message": "Conexión exitosa con cámara Hikvision",
                        "device_info": {
                            "name": device_name.text if device_name is not None else "N/A",
                            "model": model.text if model is not None else "N/A",
                            "serial": serial.text if serial is not None else "N/A",
                            "firmware": firmware.text if firmware is not None else "N/A"
                        }
                    }
                except Exception as e:
                    return {
                        "status": "success",
                        "message": "Conexión exitosa (no se pudo parsear info del dispositivo)",
                        "device_info": None
                    }
            elif response.status_code == 401:
                return {
                    "status": "error", 
                    "message": "Error de autenticación: Usuario o contraseña incorrectos"
                }
            else:
                return {
                    "status": "error", 
                    "message": f"Error {response.status_code}: {response.text[:200]}"
                }
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Timeout: La cámara no responde"}
        except requests.exceptions.ConnectionError as e:
            return {"status": "error", "message": f"Error de conexión: No se puede alcanzar la cámara - {str(e)}"}
        except Exception as e:
            return {"status": "error", "message": f"Error inesperado: {str(e)}"}
    
    def create_face_library(self, library_id: str, library_name: str):
        """Crear una biblioteca de rostros en la cámara"""
        url = f"{self.base_url}/Intelligent/FDLib"
        
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
        <FaceDataRecord>
            <id>{library_id}</id>
            <name>{library_name}</name>
        </FaceDataRecord>"""
        
        headers = {'Content-Type': 'application/xml'}
        
        try:
            print(f"[Hikvision] Creando biblioteca: {library_name} (ID: {library_id})")
            response = requests.post(url, data=xml_data, auth=self.auth, headers=headers, timeout=10, verify=False)
            
            if response.status_code in [200, 201]:
                return {"status": "success", "message": f"Biblioteca '{library_name}' creada correctamente"}
            elif response.status_code == 409:
                return {"status": "warning", "message": f"La biblioteca '{library_name}' ya existe"}
            else:
                return {"status": "error", "message": f"Error {response.status_code}: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def enroll_face(self, library_id: str, person_id: str, person_name: str, image_path: str):
        """Enrollar un rostro en la biblioteca"""
        url = f"{self.base_url}/Intelligent/FDLib/{library_id}"
        
        # Leer imagen y convertir a base64
        try:
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
        except FileNotFoundError:
            return {"status": "error", "message": f"Imagen no encontrada: {image_path}"}
        except Exception as e:
            return {"status": "error", "message": f"Error leyendo imagen: {str(e)}"}
        
        xml_data = f"""<?xml version="1.0" encoding="UTF-8"?>
        <FaceDataRecord>
            <id>{person_id}</id>
            <name>{person_name}</name>
            <faceImage>{img_data}</faceImage>
        </FaceDataRecord>"""
        
        headers = {'Content-Type': 'application/xml'}
        
        try:
            print(f"[Hikvision] Enrollando rostro: {person_name} (ID: {person_id})")
            response = requests.post(url, data=xml_data, auth=self.auth, headers=headers, timeout=15, verify=False)
            
            if response.status_code in [200, 201]:
                return {"status": "success", "message": f"Rostro de {person_name} enrollado correctamente"}
            else:
                return {"status": "error", "message": f"Error {response.status_code}: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def delete_face(self, library_id: str, person_id: str):
        """Eliminar un rostro de la biblioteca"""
        url = f"{self.base_url}/Intelligent/FDLib/{library_id}/{person_id}"
        
        try:
            print(f"[Hikvision] Eliminando rostro ID: {person_id}")
            response = requests.delete(url, auth=self.auth, timeout=10, verify=False)
            
            if response.status_code in [200, 204]:
                return {"status": "success", "message": "Rostro eliminado correctamente"}
            else:
                return {"status": "error", "message": f"Error {response.status_code}: {response.text}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_face_detection_events(self):
        """Obtener eventos de detección facial"""
        url = f"{self.base_url}/Event/triggers/FaceDetection"
        
        try:
            response = requests.get(url, auth=self.auth, timeout=10, verify=False)
            
            if response.status_code == 200:
                return {"status": "success", "data": response.text}
            else:
                return {"status": "error", "message": f"Error {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def get_snapshot(self):
        """Obtener una captura de la cámara"""
        url = f"{self.base_url}/Streaming/channels/1/picture"
        
        try:
            response = requests.get(url, auth=self.auth, timeout=10, verify=False)
            
            if response.status_code == 200:
                return {"status": "success", "image_data": response.content}
            else:
                return {"status": "error", "message": f"Error {response.status_code}"}
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Función para obtener instancia del cliente
def get_hikvision_client():
    """Obtener cliente de Hikvision con credenciales del .env"""
    camera_ip = os.getenv("HIKVISION_IP", "192.168.100.13")
    username = os.getenv("HIKVISION_USER", "admin")
    password = os.getenv("HIKVISION_PASSWORD", "Lenovob490!")
    use_https = os.getenv("HIKVISION_USE_HTTPS", "false").lower() == "true"
    
    return HikvisionClient(camera_ip, username, password, use_https)