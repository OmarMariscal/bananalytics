import os
from datetime import datetime #Para generar fechas de registro
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
#Importación de SQLAlchemy para la conexión a Neon (BD)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from models import Store

#----------------------------- MODELOS DE DATOS -----------------------------
# Molde para los productos individuales
class ProductoRecibido(BaseModel):
    barcode: str
    amount: int

# Molde para cada bloque de hora (ej. 12:30:00)
class VentaPorHora(BaseModel):
    time: str
    products: List[ProductoRecibido]

# Molde principal que atrapa todo el JSON del frontend
class SincronizacionMensaje(BaseModel):
    id_store: int
    date: str
    day: int
    sales: List[VentaPorHora]

# Molde para el registro de un nuevo negocio
class RegistroNegocio(BaseModel):
    name: str
    email: str
    city: str
    lat: float
    lng: float
#-------------------------------------------------------------------------------

load_dotenv()

app = FastAPI()

#Definimos que la llave debe venir en el header llamado "X-API-Key"
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

#Leemos la contraseña correcta desde nuestro archivo .env
SECRET_KEY = os.getenv("API_KEY")

#Cargar la URL de conexión desde el .env para la conexión a Neon
DATABASE_URL = os.getenv("DATABASE_URL")

# Creamos el motor y la sesión
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependencia: Esto abre la conexión a la base de datos cada que llega una petición y la cierra al terminar
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#Verifica si la llave que envían es la correcta
def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: API Key inválida"
        )
    return api_key

#-------------------------------------------------- ENDPOINTS ----------------------------------------------

#Ruta de Salud (No necesita autenticación)******************************************************************
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "online",
        "version": "1.0",
        "base_datos": "conectada"
    }

#Registrar un nuevo negocio (Necesita autenticación con API Key)********************************************
@app.post("/api/v1/business/register", dependencies=[Depends(verify_api_key)])
def register_business(datos: RegistroNegocio, db: Session = Depends(get_db)): #Se guarda el json en la variable "datos" con el molde definido en la clase "RegistroNegocio". Además, se inyecta la sesión de la base de datos con "db" para usarla dentro de la función
    try:
        #Verificar si el correo ya existe haciendo una consulta a la tabla Store buscando el email
        tienda_existente = db.query(Store).filter(Store.email == datos.email).first()
        
        if tienda_existente:
            return {
                "status": "email_repeated",
                "id_negocio": None,
                "mensaje": "El correo ya se encuentra registrado."
            }

        #Si no existe, preparamos el nuevo registro para la base de datos
        nueva_tienda = Store(
            owner_name=datos.name,
            email=datos.email,
            city=datos.city,
            latitude=datos.lat,
            longitude=datos.lng,
            registration_time=datetime.now() # Capturamos la hora actual
        )

        #Guardamos en PostgreSQL
        db.add(nueva_tienda)
        db.commit()
        
        #Refrescamos para que PostgreSQL nos devuelva el "store_id" que generó automáticamente
        db.refresh(nueva_tienda)

        return {
            "status": "exito",
            "id_negocio": str(nueva_tienda.store_id), #Lo mandamos como texto
            "mensaje": "Negocio registrado correctamente. Coordenadas ancladas para el modelo predictivo."
        }

    except Exception as e:
        #Si algo falla, deshacemos los cambios y enviamos error
        db.rollback()
        return {
            "status": "fail",
            "id_negocio": None,
            "mensaje": f"Error de conexión con el servidor: {str(e)}"
        }

#Sincronizar Ventas (Necesita autenticación con API Key)****************************************************
@app.post("/api/v1/ventas/sync", dependencies=[Depends(verify_api_key)])
def sync_ventas(datos: SincronizacionMensaje): #Se guarda el json en la variable "datos" con el molde definido en la clase "SincronizacionMensaje"
    
    #Guardamos los datos del encabezado del mensaje en variables para usarlas luego
    tienda_id = datos.id_store
    fecha = datos.date
    #Servira para validar que el servidor local nos envió todo lo que debía enviar
    total_bloques_hora = len(datos.sales)
    
    #Aquí irá la conexió a la API del Clima

    #Aquí irá la conexió a la API de Códigos de Barras
    
    #Aquí insertaré todo a la base de datos Neon usando SQLAlchemy
    
    #se devuelve una respuesta
    return {
        "status": "exito",
        "ventas_recibidas": total_bloques_hora,
        "ventas_procesadas": 0, # Esto lo cambiarás luego cuando hagas el procesamiento
        "mensaje": f"Se recibieron datos de la tienda {tienda_id} para la fecha {fecha}"
    }