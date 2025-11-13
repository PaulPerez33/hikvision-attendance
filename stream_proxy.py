# stream_proxy.py
from flask import Flask, Response
import requests
from requests.auth import HTTPDigestAuth

app = Flask(__name__)

CAMERA_IP = "192.168.100.13"
CAMERA_USER = "admin"
CAMERA_PASSWORD = "Lenovob490!"

@app.route('/stream')
def stream():
    stream_url = f"http://{CAMERA_IP}/ISAPI/Streaming/channels/1/httpPreview"
    
    def generate():
        r = requests.get(
            stream_url,
            auth=HTTPDigestAuth(CAMERA_USER, CAMERA_PASSWORD),
            stream=True
        )
        for chunk in r.iter_content(chunk_size=1024):
            yield chunk
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)