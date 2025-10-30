# app/create_tables.py
from app.db import engine, Base
# importa tus modelos para que Base conozca las tablas
from app import models  # asume que app/models.py define las clases y usa Base

def main():
    print("Creando tablas en la BD...")
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente.")

if __name__ == "__main__":
    main()
