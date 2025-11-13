from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, stream, students, teacher_notes, camera, auth, attendance, dashboard

app = FastAPI(title="HikSchool Attendance API")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend React
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(teacher_notes.router)
app.include_router(camera.router)
app.include_router(attendance.router)
app.include_router(dashboard.router)
app.include_router(stream.router)

@app.get("/")
def root():
    return {"status": "ok", "message": "HikSchool Attendance API"}