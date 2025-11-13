# app/seed_demo_data.py
"""
Script para llenar la base de datos con datos de demostración realistas
"""
from app.db import SessionLocal, engine, Base
from app import models
from app.auth import get_password_hash
from datetime import datetime, timedelta
import random

def clear_all_data(db):
    """Limpiar toda la data existente (CUIDADO en producción)"""
    print("🗑️  Limpiando datos existentes...")
    db.query(models.TeacherNote).delete()
    db.query(models.Attendance).delete()
    db.query(models.Student).delete()
    db.query(models.User).delete()
    db.commit()
    print("✅ Datos limpiados")

def create_users(db):
    """Crear usuarios de demostración"""
    print("\n👥 Creando usuarios...")
    
    users = [
        {
            "username": "directora",
            "full_name": "Martha Elena Rodríguez",
            "role": "admin",
            "password": "directora123"
        },
        {
            "username": "prof_matematicas",
            "full_name": "Carlos Alberto Méndez",
            "role": "teacher",
            "password": "profesor123"
        },
        {
            "username": "prof_ciencias",
            "full_name": "Laura Patricia Hernández",
            "role": "teacher",
            "password": "profesor123"
        }
    ]
    
    created_users = []
    for user_data in users:
        user = models.User(
            username=user_data["username"],
            full_name=user_data["full_name"],
            role=user_data["role"],
            hashed_password=get_password_hash(user_data["password"])
        )
        db.add(user)
        created_users.append(user)
    
    db.commit()
    for user in created_users:
        db.refresh(user)
    
    print(f"✅ Creados {len(created_users)} usuarios")
    return created_users

def create_students(db):
    """Crear estudiantes de demostración"""
    print("\n👨‍🎓 Creando estudiantes...")
    
    nombres = [
        ("Juan", "García López"), ("María", "Martínez Sánchez"), ("Carlos", "Rodríguez Torres"),
        ("Ana", "López Ramírez"), ("Luis", "Hernández Pérez"), ("Sofía", "González Morales"),
        ("Miguel", "Díaz Flores"), ("Valentina", "Sánchez Ruiz"), ("Diego", "Torres Castro"),
        ("Isabella", "Ramírez Ortiz"), ("Alejandro", "Morales Gutiérrez"), ("Camila", "Flores Herrera"),
        ("Daniel", "Castro Vargas"), ("Lucía", "Ortiz Medina"), ("Andrés", "Gutiérrez Reyes"),
        ("Gabriela", "Herrera Jiménez"), ("José", "Vargas Ramos"), ("Fernanda", "Medina Cruz"),
        ("Roberto", "Reyes Mendoza"), ("Paula", "Jiménez Aguilar"), ("Ricardo", "Ramos Soto"),
        ("Daniela", "Cruz Vega"), ("Jorge", "Mendoza Silva"), ("Adriana", "Aguilar Cortés"),
        ("Fernando", "Soto Paredes"), ("Carolina", "Vega Romero"), ("Pedro", "Silva Navarro"),
        ("Natalia", "Cortés Guerrero"), ("Manuel", "Paredes León"), ("Andrea", "Romero Campos"),
        ("Raúl", "Navarro Muñoz"), ("Mariana", "Guerrero Santos"), ("Alberto", "León Ríos"),
        ("Paola", "Campos Fuentes"), ("Eduardo", "Muñoz Domínguez"), ("Valeria", "Santos Rojas"),
        ("Héctor", "Ríos Delgado"), ("Claudia", "Fuentes Castillo"), ("Sergio", "Domínguez Contreras"),
        ("Patricia", "Rojas Salazar"), ("Arturo", "Delgado Peña"), ("Verónica", "Castillo Mora"),
        ("Javier", "Contreras Luna"), ("Sandra", "Salazar Molina"), ("Oscar", "Peña Estrada"),
        ("Mónica", "Mora Núñez"), ("Ernesto", "Luna Zavala"), ("Elena", "Molina Carrillo"),
        ("Hugo", "Estrada Acosta"), ("Gloria", "Núñez Ibarra")
    ]
    
    niveles = ["secundaria", "secundaria", "secundaria", "preparatoria", "preparatoria"]
    
    created_students = []
    for i, (nombre, apellido) in enumerate(nombres, 1):
        student = models.Student(
            first_name=nombre,
            last_name=apellido,
            photo_path=f"/photos/{nombre.lower()}_{apellido.split()[0].lower()}.jpg",
            grade_level=random.choice(niveles)
        )
        db.add(student)
        created_students.append(student)
    
    db.commit()
    for student in created_students:
        db.refresh(student)
    
    print(f"✅ Creados {len(created_students)} estudiantes")
    return created_students

def create_attendances(db, students):
    """Crear registros de asistencia de los últimos 30 días"""
    print("\n📅 Creando registros de asistencia...")
    
    today = datetime.now()
    count = 0
    
    # Simular asistencias de los últimos 30 días
    for days_ago in range(30):
        date = today - timedelta(days=days_ago)
        
        # Simular que es día laboral (lunes a viernes)
        if date.weekday() >= 5:  # 5=sábado, 6=domingo
            continue
        
        # 85-95% de estudiantes asisten cada día
        attending_students = random.sample(students, k=int(len(students) * random.uniform(0.85, 0.95)))
        
        for student in attending_students:
            # Hora aleatoria de entrada (7:00 AM - 8:30 AM)
            hour = random.randint(7, 8)
            minute = random.randint(0, 59)
            timestamp = date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            attendance = models.Attendance(
                student_id=student.id,
                timestamp=timestamp,
                camera_id="camera_entrance_01",
                matched=True
            )
            db.add(attendance)
            count += 1
    
    db.commit()
    print(f"✅ Creados {count} registros de asistencia")

def create_teacher_notes(db, students, teachers):
    """Crear notas de maestros"""
    print("\n📝 Creando notas de maestros...")
    
    categorias = ["academico", "social", "deportivo", "artistico"]
    
    notas_ejemplos = {
        "academico": [
            "Demuestra excelente comprensión de conceptos matemáticos avanzados.",
            "Muestra gran interés en las ciencias naturales y hace preguntas pertinentes.",
            "Excelente desempeño en la resolución de problemas lógicos.",
            "Necesita reforzar sus habilidades de lectura comprensiva.",
            "Destaca por su capacidad de análisis crítico en las discusiones.",
            "Presenta trabajos bien estructurados y con buena investigación.",
            "Tiene facilidad para aprender idiomas, especialmente inglés.",
            "Muestra creatividad al resolver ejercicios matemáticos.",
        ],
        "social": [
            "Excelente trabajo en equipo, siempre apoya a sus compañeros.",
            "Demuestra liderazgo natural en actividades grupales.",
            "Es muy participativo en clase y genera buen ambiente.",
            "Necesita mejorar su comunicación con otros estudiantes.",
            "Destaca por su empatía y solidaridad con los demás.",
            "Muestra respeto y buenos modales con maestros y compañeros.",
            "Tiene habilidades de mediación en conflictos entre compañeros.",
        ],
        "deportivo": [
            "Excelente desempeño en educación física y deportes.",
            "Muestra gran coordinación motriz y habilidades atléticas.",
            "Demuestra disciplina y compromiso en actividades deportivas.",
            "Destaca en deportes de equipo como fútbol y básquetbol.",
            "Tiene potencial para competencias deportivas.",
            "Muestra interés en actividades físicas y vida saludable.",
        ],
        "artistico": [
            "Talento destacado en artes visuales y dibujo.",
            "Muestra sensibilidad artística y creatividad.",
            "Excelente participación en actividades culturales.",
            "Tiene habilidades musicales, toca instrumentos.",
            "Destaca en presentaciones teatrales y expresión oral.",
            "Muestra interés y talento en diseño y creatividad visual.",
        ]
    }
    
    count = 0
    # Crear 3-5 notas aleatorias para cada estudiante
    for student in students:
        num_notes = random.randint(3, 5)
        for _ in range(num_notes):
            categoria = random.choice(categorias)
            nota = random.choice(notas_ejemplos[categoria])
            teacher = random.choice([t for t in teachers if t.role == "teacher"])
            
            # Fecha aleatoria en los últimos 60 días
            days_ago = random.randint(1, 60)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            note = models.TeacherNote(
                student_id=student.id,
                teacher_id=teacher.id,
                note=nota,
                category=categoria,
                timestamp=timestamp
            )
            db.add(note)
            count += 1
    
    db.commit()
    print(f"✅ Creadas {count} notas de maestros")

def main():
    """Función principal para ejecutar el seed"""
    print("="*60)
    print("🌱 SEED DE DATOS DE DEMOSTRACIÓN")
    print("="*60)
    
    # Crear sesión de base de datos
    db = SessionLocal()
    
    try:
        # Limpiar datos existentes
        response = input("\n⚠️  ¿Deseas ELIMINAR todos los datos existentes? (s/n): ")
        if response.lower() == 's':
            clear_all_data(db)
        
        # Crear datos de demostración
        users = create_users(db)
        students = create_students(db)
        create_attendances(db, students)
        create_teacher_notes(db, students, users)
        
        print("\n" + "="*60)
        print("✅ SEED COMPLETADO EXITOSAMENTE")
        print("="*60)
        print("\n📊 Resumen:")
        print(f"  - Usuarios: {len(users)} (1 admin, 2 maestros)")
        print(f"  - Estudiantes: {len(students)}")
        print(f"  - Asistencias: ~{len(students) * 25} registros")
        print(f"  - Notas: ~{len(students) * 4} notas de maestros")
        print("\n🔐 Credenciales de acceso:")
        print("  Directora:")
        print("    Usuario: directora")
        print("    Contraseña: directora123")
        print("\n  Profesores:")
        print("    Usuario: prof_matematicas")
        print("    Contraseña: profesor123")
        print("\n    Usuario: prof_ciencias")
        print("    Contraseña: profesor123")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()