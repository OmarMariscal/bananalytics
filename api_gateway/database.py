import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
from models import Base  # Importa las tablas de models.py

#Cargar la URL de conexión desde el .env
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

#Crear el "motor" que se conecta a Neon con protección anti-desconexiones SSL
es_desarrollo = os.environ.get("DEBUG", "false").lower() == "true" #Cambiar a false cuando dejemos de hacer pruebas locales para evitar el exceso de logs en producción

engine = create_engine(
    DATABASE_URL, 
    echo=es_desarrollo, 
    pool_pre_ping=True, 
    pool_recycle=300
)

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