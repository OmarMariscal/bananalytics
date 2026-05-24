import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker #Para crear sesiones de base de datos
from dotenv import load_dotenv
from models import Base  # Importa las tablas de models.py

#Cargar la URL de conexión desde el .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

#Crear el único "motor" que se conecta a Neon para todo el proyecto
engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    pool_recycle=300
)

# Fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Función para generar las tablas
def init_db():
    print("Conectando a Neon y borrando tablas viejas...")
    Base.metadata.drop_all(bind=engine) #ELiminamos tablas viejas para crearlas de nuevo con las nuevas características

    print("Creando tablas nuevas con la arquitectura actualizada...")
    #traducción de clases de Python a SQL y las ejecuta en Neon
    Base.metadata.create_all(bind=engine)
    print("¡Tablas creadas exitosamente!")

if __name__ == "__main__":
    init_db()