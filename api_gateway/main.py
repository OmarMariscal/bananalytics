import os
import requests
from datetime import datetime, date #Para generar fechas de registro
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List
#Importación de SQLAlchemy para la conexión a Neon (BD)
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, Session
#Importamos las clases de la base de datos para hacer consultas e inserciones
from models import Store, Product, Sale, Prediction

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

#Cargar la llave de la API de códigos de barras desde el .env
GOUPC_API_KEY = os.getenv("GOUPC_API_KEY")

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

#-------------------------------------------------- FUNCIONES AUXILIARES ----------------------------------------------

#Función para procesar la cola de ventas en segundo plano**************************************************************
def procesar_y_guardar_ventas(datos: SincronizacionMensaje, latitud: float, longitud: float):
    # Esta función corre en el fondo. El cliente local NO se queda esperando a que termine.
    tienda_id = datos.id_store
    
    # Imprimimos en consola para ver que sí está trabajando
    print(f"Empezando a procesar en segundo plano el JSON de la tienda {tienda_id}...")
    
    db: Session = SessionLocal()
    try:
        #Formatear la fecha de "DD-MM-YYYY" a "YYYY-MM-DD"
        fecha_obj = datetime.strptime(datos.date, "%d-%m-%Y")
        fecha_open_meteo = fecha_obj.strftime("%Y-%m-%d")

        #Conexión a la API Histórica de Open-Meteo====================================================================
        #Se decidió conservar la consulta en URL en vez de usar su librería especializada porque es una consulta sencilla y se reduce la cantidad de dependencias 
        print("Consultando clima histórico en Open-Meteo...")
        url_clima = "https://archive-api.open-meteo.com/v1/archive"

        parametros = {
            "latitude": latitud, #Usamos las coordenadas pasadas como parámetros a la función
            "longitude": longitud,
            "start_date": fecha_open_meteo,
            "end_date": fecha_open_meteo,
            "hourly": "temperature_2m,weather_code", #Pedimos temperatura y código de clima
            "timezone": "auto" #Ajusta las horas a la zona horaria local de las coordenadas
        }

        respuesta = requests.get(url_clima, params=parametros)
        respuesta.raise_for_status() # Lanza un error si la API falla
        
        datos_clima = respuesta.json()

        #Extraemos las listas de datos (cada lista tiene 24 elementos, uno por hora del día)
        horas_clima = datos_clima["hourly"]["time"]
        temperaturas = datos_clima["hourly"]["temperature_2m"]
        codigos_clima = datos_clima["hourly"]["weather_code"]
        
        print(f"¡Clima obtenido con éxito para la fecha {fecha_open_meteo}!")

        #Conexión a la API de Go UPC para obtener información de los productos=========================================
        print("Procesando códigos de barras y preparando inserciones...")
        for bloque_venta in datos.sales:
            #Emparejamos la hora para solo tener el número de hora (ej. 12) y no la hora completa (ej. 12:30:00)
            hora_texto = bloque_venta.time.split(":")[0] 
            indice_hora = int(hora_texto)

            # Usamos ese índice para sacar el clima exacto de ese bloque
            temp_actual = temperaturas[indice_hora]
            codigo_clima_actual = str(codigos_clima[indice_hora]) # Convertimos a String 

            #Recorremos cada producto dentro de ese bloque
            for producto_recibido in bloque_venta.products:
                codigo = producto_recibido.barcode

                #Llamamos a nuestra función ayudante y le pasamos el código y nuestra sesión "db"
                producto_info = obtener_o_crear_producto(codigo, db)

                #Preparamos el registo para la tabla sales_database
                nueva_venta = Sale(
                    store_id=tienda_id,
                    barcode=codigo,
                    date=fecha_open_meteo, #Formato YYYY-MM-DD
                    time=bloque_venta.time, #Guardamos la hora exacta: "12:30:00"
                    amount=producto_recibido.amount,
                    temperature=temp_actual,
                    weather_resume=codigo_clima_actual
                )
                db.add(nueva_venta)
            
        # Hacemos el commit una sola vez al final del ciclo para guardar todas las ventas de golpe
        db.commit()
        print(f"¡Se han guardado exitosamente todas las ventas de la tienda {tienda_id}!")

    except Exception as e:
        print(f"Error al procesar las ventas de la tienda {tienda_id}: {str(e)}")
        db.rollback()
    
    finally:
        db.close()
        print(f"Terminó de guardar los datos de la tienda {tienda_id} en PostgreSQL.")

#Función para buscar el producto en Neon, o lo descarga de Go UPC******************************************************
def obtener_o_crear_producto(barcode: str, db: Session):
    #Buscamos en nuestra base de datos central primero
    producto_existente = db.query(Product).filter(Product.barcode == barcode).first()
    
    #Si ya lo conocemos, lo devolvemos inmediatamente sin gastar saldo de API
    if producto_existente:
        return producto_existente

    #Si no existe, entonces consultamos a GO UPC
    print(f"Código {barcode} no existe en Neon. Consultando GO UPC...")
    url = f"https://go-upc.com/api/v1/code/{barcode}"
    
    headers = {
        "Authorization": f"Bearer {GOUPC_API_KEY}"
    }
    
    try:
        respuesta = requests.get(url, headers=headers)
        
        #Si el producto no está registrado, Go UPC devuelve 404
        if respuesta.status_code == 404:
            print(f"Advertencia: Producto {barcode} no encontrado.")
            nuevo_producto = Product(
                barcode=barcode,
                product_name="Producto Desconocido",
                category="Sin Categoría",
                image_url="Sin Imagen"
            )
        else:
            # Si todo salió bien, extraemos los datos
            respuesta.raise_for_status()
            datos_api = respuesta.json()
            info_producto = datos_api.get("product", {})
            
            nuevo_producto = Product(
                barcode=barcode,
                product_name=info_producto.get("name", "Nombre no disponible"),
                category=info_producto.get("category", "Sin Categoría"),
                image_url=info_producto.get("imageUrl", "Sin Imagen")
            )
            print(f"¡Producto {nuevo_producto.product_name} descargado de GO UPC!")

        #Lo guardamos en Neon para la próxima vez
        db.add(nuevo_producto)
        db.commit()
        db.refresh(nuevo_producto)
        
        return nuevo_producto

    except Exception as e:
        print(f"Error al conectar con GO UPC para {barcode}: {str(e)}")
        #Para no frenar el programa si la API se cae, devolvemos un genérico
        return None
    

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
def sync_ventas(
    datos: SincronizacionMensaje,  #Se guarda el json en la variable "datos" con el molde definido en la clase "SincronizacionMensaje"
    background_tasks: BackgroundTasks, #Inyectamos la cola de tareas en segundo plano para no hacer esperar al cliente local mientras procesamos el JSON
    db: Session = Depends(get_db) #Conectamos la base de datos al endpoint para realizar una validación
    ):

    #Validación:Buscar la tienda en la base de datos
    tienda_existente = db.query(Store).filter(Store.store_id == datos.id_store).first()

    #Si la consulta regresa vacía (None), la tienda no existe
    if not tienda_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Error: La tienda con ID {datos.id_store} no está registrada en el servidor."
        )#Si la tienda existe, seguimos con el procesamiento normal del endpoint

    #Guardamos los datos del encabezado del mensaje epara armar la respuesta rápida
    tienda_id = datos.id_store
    fecha = datos.date
    #Servira para validar que el servidor local nos envió todo lo que debía enviar
    total_bloques_hora = len(datos.sales)

    #FastAPI formará una cola de tareas en segundo plano. pasandole el json completo a la función "procesar_y_guardar_ventas"
    background_tasks.add_task(procesar_y_guardar_ventas, datos, float(tienda_existente.latitude), float(tienda_existente.longitude))
    
    #se devuelve una respuesta en milisegundos
    return {
        "status": "exito",
        "ventas_recibidas": total_bloques_hora,
        "ventas_procesadas": 0, # Esto lo cambiarás luego cuando hagas el procesamiento
        "mensaje": f"Se recibieron datos de la tienda {tienda_id} para la fecha {fecha}"
    }

#Obtener Predicciones por Tienda (Necesita autenticación con API Key)***************************************
@app.get("/api/v1/business/{store_id}/predictions", dependencies=[Depends(verify_api_key)])
def get_predictions(store_id: int, db: Session = Depends(get_db)):
    
    # Obtenemos la fecha actual del servidor
    hoy = date.today()

    #Hacemos un JOIN entre Prediction y Product usando el barcode como puente
    resultados = db.query(Prediction, Product).join(
        Product, Prediction.barcode == Product.barcode
    ).filter(
        Prediction.store_id == store_id,
        Prediction.objetive_date > hoy  #que la fecha de objetivo sea mayor a la de hoy
    ).all()

    respuesta = []
    
    #"pred" contiene los datos de la predicción, "prod" los datos del producto
    for pred, prod in resultados:
        respuesta.append({
            "product_name": prod.product_name,
            "Category": prod.category,
            "image_url": prod.image_url,
            "objetive_date": pred.objetive_date.strftime("%Y-%m-%d"), # Convertimos la fecha a texto
            "prediction": pred.prediction,
            "percentage_average_deviation": pred.percentage_average_deviation,
            "feature": pred.feature,
            "type": pred.type
        })
        
    return respuesta

#Obtener Historial de Ventas de un Producto Específico (Necesita autenticación con API Key)*****************
@app.get("/api/v1/business/{store_id}/{barcode}", dependencies=[Depends(verify_api_key)])
def get_sales_history(store_id: int, barcode: str, db: Session = Depends(get_db)):
    
    #Agrupamos por fecha y suma las cantidades de la base de datos, filtrando por tienda y código de barras.
    resultados = db.query(
        Sale.date.label("fecha"), 
        func.sum(Sale.amount).label("total_vendido")
    ).filter(
        Sale.store_id == store_id,
        Sale.barcode == barcode
    ).group_by(
        Sale.date
    ).order_by(
        Sale.date #Las ordenamos cronológicamente
    ).all()

    #Armamos la respuesta en el formato que espera el frontend
    respuesta = []
    
    for fila in resultados:
        respuesta.append({
            "fecha": fila.fecha.strftime("%Y-%m-%d"),
            "total_vendido": fila.total_vendido
        })
        
    return respuesta