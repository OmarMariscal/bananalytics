import json
import os
from operator import truediv

from database import obtener_conexion
from datetime import datetime

ARCHIVO_CONFIG = "config.json"
ARCHIVO_COLA = "missing-items.txt"

def leer_config():
    if not os.path.exists(ARCHIVO_CONFIG):
        config_default = {"id_store": 1}
        with open(ARCHIVO_CONFIG, "w") as archivo:
            json.dump(config_default, archivo)
        print("Config creado con valores default")

    with open(ARCHIVO_CONFIG, "r") as archivo:
        config = json.load(archivo)

    return config

def empaquetar_ventas():
    config = leer_config()

    hoy = datetime.now()
    date = hoy.strftime("%d-%m-%Y")
    day = hoy.weekday() + 1

    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("SELECT barcode, time, amount FROM sales_now")
    filas = cursor.fetchall()

    conexion.close()

    if not filas:
        print("No hay ventas para empaquetar")
        return None


    transacciones = {}

    for fila in filas:
        barcode = fila[0]
        time = fila[1]
        amount = fila[2]


        if time not in transacciones:
            transacciones[time] = {
                "time": time,
                "products": []
            }


        transacciones[time]["products"].append({
            "barcode": barcode,
            "amount": amount
        })


    paquete = {
        "id_store": config["id_store"],
        "date": date,
        "day": day,
        "sales": list(transacciones.values())
    }
    print(f"Paquete armado: {json.dumps(paquete, indent=2)}")
    return paquete

def enviar_paquete(paquete):
    import requests

    URL_SERVIDOR = "http://localhost:9000/api/v1/ventas/sync"

    API_KEY = "tu_clave_secreta"

    try:
        respuesta = requests.post(URL_SERVIDOR,
                                  json=paquete,
                                  data={"key": API_KEY},
                                  timeout=10
                                  )
        if respuesta.status_code == 200:
            print(f"Envio exitoso: {respuesta.json()}")
            return True
        else:
            print(f"Error del servidor: {respuesta.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        print("Sin conexion, guardando en cola")
        return False

    except requests.exceptions.Timeout:
        print("Timeout. guardando en cola")
        return False

def vaciar_sqlite():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM sales_now")

    conexion.commit()

    conexion.close()
    print("SQLite vaciado correctamente")

def guardar_en_cola(paquete):
    linea = json.dumps(paquete)

    with open(ARCHIVO_COLA, "a") as arhivo:
        arhivo.write(linea + "\n")

        print(f"JSON guardado en cola: {ARCHIVO_COLA}")

def sincronizacion_nocturna():
    print("Iniciando sincronizacion nocturna...")

    paquete = empaquetar_ventas()

    if paquete is None:
        print("Nada que sincronizar, terminando")
        return

    envio_exitoso = enviar_paquete(paquete)

    if envio_exitoso:
        vaciar_sqlite()
        print("Sincronizacion completada exitosamente")
    else:
        guardar_en_cola(paquete)
        print("Sincronizacion fallida, JSON en cola de reenvio")

def procesar_cola_pendientes():
    if not os.path.exists(ARCHIVO_COLA) or os.stat(ARCHIVO_COLA).st_size == 0:
        return

    with open(ARCHIVO_COLA, "r") as archivo:
        lineas = archivo.readlines()

    lineas_pendientes = []
    conexion_activa = True

    print(f"Intentando reenviar {len(lineas)} paquetes atrasados de la cola...")

    for linea in lineas:
        if not linea.strip():
            continue

        if not conexion_activa:
            lineas_pendientes.append(linea)
            continue

        try:
            paquete = json.loads(linea)
            import requests

            respuesta = requests.post(
                "http://127.0.0.1:8000/api/v1/simulador-nube/sync",
                json=paquete,
                headers={"X-API-Key": "tu_clave_secreta"},
                timeout=10
            )

            if respuesta.status_code == 200:
                print("Paquete atrasado enviado exitosamente al servidor.")
            else:
                print(f"Error del Servidor ({respuesta.status_code}). Se mantiene en cola")
                lineas_pendientes.append(linea)

        except requests.exceptions.RequestException:
            print("La red sigue caida. Pausando el reenvio.")
            conexion_activa = False
            lineas_pendientes.append(linea)

    with open(ARCHIVO_COLA, "w") as archivo:
        for linea_pendiente in lineas_pendientes:
            archivo.write(linea_pendiente)