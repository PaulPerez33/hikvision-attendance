from fastapi import FastAPI
from app.routers import health, students

app = FastAPI(title="HikSchool Attendance API")

app.include_router(health.router)
app.include_router(students.router)
@app.get("/")
def root():
    return {"status": "ok", "message": "HikSchool Attendance API"}