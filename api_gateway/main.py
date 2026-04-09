import os
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List

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
#-------------------------------------------------------------------------------

load_dotenv()

app = FastAPI()

#Definimos que la llave debe venir en el header llamado "X-API-Key"
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

#Leemos la contraseña correcta desde nuestro archivo .env
SECRET_KEY = os.getenv("API_KEY")

#Verifica si la llave que envían es la correcta
def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Acceso denegado: API Key inválida"
        )
    return api_key

#----------------------------- ENDPOINTS -----------------------------

#Ruta de Salud (No necesita autenticación)
@app.get("/api/v1/health")
def health_check():
    return {
        "status": "online",
        "version": "1.0",
        "base_datos": "conectada"
    }

#Sincronizar Ventas (Necesita autenticación con API Key)
@app.post("/api/v1/ventas/sync", dependencies=[Depends(verify_api_key)])
def sync_ventas(datos: SincronizacionMensaje): #Se guarda el json en la variable "datos" con el molde que definimos arriba
    
    #Guardamos los datos del encabezado del mensaje en variables para usarlas luego
    tienda_id = datos.id_store
    fecha = datos.date
    #Servira para validar que el frontend nos envió todo lo que debía enviar
    total_bloques_hora = len(datos.sales)
    
    #Aquí irá la conexió a la API del Clima

    #Aquí irá la conexió a la API de Códigos de Barras
    
    #Aquí insertaré todo a la base de datos Neon usando SQLAlchemy
    
    # se devuelve una respuesta
    return {
        "status": "exito",
        "ventas_recibidas": total_bloques_hora,
        "ventas_procesadas": 0, # Esto lo cambiarás luego cuando hagas el procesamiento
        "mensaje": f"Se recibieron datos de la tienda {tienda_id} para la fecha {fecha}"
    }