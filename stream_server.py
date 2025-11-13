# stream_server.py
from flask import Flask, Response
from flask_cors import CORS
import requests
from requests.auth import HTTPDigestAuth

app = Flask(__name__)
CORS(app)  # Permitir acceso desde React

# Credenciales de la cámara
CAMERA_IP = "192.168.100.13"
CAMERA_USER = "admin"
CAMERA_PASSWORD = "Lenovob490!"

@app.route('/stream')
def video_feed():
    """Endpoint de streaming de video"""
    
    # Probar diferentes canales hasta que uno funcione
    channels = [
        f"http://{CAMERA_IP}/ISAPI/Streaming/channels/1/httpPreview",
        f"http://{CAMERA_IP}/ISAPI/Streaming/channels/101/httpPreview",
        f"http://{CAMERA_IP}/ISAPI/Streaming/channels/1",
    ]
    
    for url in channels:
        try:
            print(f"[Stream] Intentando canal: {url}")
            
            def generate():
                r = requests.get(
                    url,
                    auth=HTTPDigestAuth(CAMERA_USER, CAMERA_PASSWORD),
                    stream=True,
                    timeout=10
                )
                
                print(f"[Stream] Respuesta: {r.status_code}")
                print(f"[Stream] Content-Type: {r.headers.get('Content-Type')}")
                
                if r.status_code == 200:
                    for chunk in r.iter_content(chunk_size=4096):
                        if chunk:
                            yield chunk
            
            return Response(
                generate(),
                mimetype='multipart/x-mixed-replace; boundary=--myboundary'
            )
        
        except Exception as e:
            print(f"[Stream] Error con {url}: {str(e)}")
            continue
    
    return "No se pudo conectar con ningún canal", 500

@app.route('/snapshot')
def snapshot():
    """Endpoint de captura estática"""
    snapshot_url = f"http://{CAMERA_IP}/ISAPI/Streaming/channels/1/picture"
    
    try:
        r = requests.get(
            snapshot_url,
            auth=HTTPDigestAuth(CAMERA_USER, CAMERA_PASSWORD),
            timeout=5
        )
        
        if r.status_code == 200:
            return Response(r.content, mimetype='image/jpeg')
        else:
            return f"Error {r.status_code}", 500
    
    except Exception as e:
        return str(e), 500

@app.route('/health')
def health():
    return {"status": "ok", "camera_ip": CAMERA_IP}

if __name__ == '__main__':
    print("="*60)
    print("🎥 Servidor de Stream de Cámara Hikvision")
    print("="*60)
    print(f"📹 Cámara: {CAMERA_IP}")
    print(f"🌐 Servidor corriendo en: http://localhost:5000")
    print(f"📺 Stream disponible en: http://localhost:5000/stream")
    print(f"📸 Snapshot disponible en: http://localhost:5000/snapshot")
    print("="*60)
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)