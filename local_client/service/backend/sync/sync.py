import json
import os
import time
import threading
import requests
from datetime import datetime
from service.backend.db.sqlite_manager import SQLiteManager

class SyncDaemon:
    #Constructor del Daemon, recibe la conexion a la base de datos y define rutas de los archivos locales y la URL de la nube
    def __init__(self, db: SQLiteManager):
        self.db = db
        self.archivo_cola = "missing-items.txt"
        self.archivo_config = "settings.json"
        self.api_url = "https://bananalytics.onrender.com/api/v1/ventas/sync"
        self.api_key = "tu_clave_secreta"

    def start(self):
        """Inicia el ciclo infinito en un hilo separado para no congelar la UI de Flet."""
        hilo = threading.Thread(target=self._ciclo_infinito, daemon=True)
        hilo.start()
        print("Daemon de sincronizacion iniciado en segundo plano")

    #Intenta mandar los archivos atrasados en cola pendientes. Una vez sean las 12, intenta mandar las ventas empaquetadas del dia
    def _ciclo_infinito(self):
        time.sleep(5)
        while True:
            self.procesar_cola_pendientes()
            hora_actual = datetime.now().hour
            if hora_actual == 0:
                print("Iniciando cierre de caja automatico...")
                self.sincronizacion_nocturna()
                time.sleep(3600)

            time.sleep(1800)

    #Busca el archivo settings.json para averiguar el ID de la tienda
    def leer_config(self):
        if not os.path.exists(self.archivo_config): #Si el archivo no existe, se crea uno de emergencia
            config_default = {
                "system": {"first_launch_completed": False},
                "store_profile": {"id_store": 1}
            }
            with open(self.archivo_config, "w") as archivo:
                json.dump(config_default, archivo, indent=4)
            print("Config creado con valores default")

        with open(self.archivo_config, "r") as archivo:
            return json.load(archivo)

    #Saca todo lo del SQLite y lo convierte en el JSON esperado por Angel
    def empaquetar_ventas(self):
        config = self.leer_config()
        id_store = config.get("store_profile", {}).get("id_store", 1)

        hoy = datetime.now()
        date_str = hoy.strftime("%d-%m-%Y")
        day = hoy.weekday() + 1

        conexion = self.db.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT barcode, time, amount FROM sales_now")
        filas = cursor.fetchall()
        conexion.close()

        if not filas:
            print("No hay ventas locales para empaquetar en SQLite")
            return None

        transacciones = {}
        for fila in filas:
            barcode, hora_venta, amount = fila[0], fila[1], fila[2]

            if hora_venta not in transacciones: #Agrupa los productos escaneados bajo la misma hora de venta
                transacciones[hora_venta] = {
                    "time": hora_venta,
                    "products": []
                }
            transacciones[hora_venta]["products"].append({
                "barcode": barcode,
                "amount": amount
            })

        paquete = {
            "id_store": id_store,
            "date": date_str,
            "day": day,
            "sales": list(transacciones.values())
        }
        return paquete

    #Intenta mandar la caja a la nube
    def enviar_paquete(self, paquete):
        headers = {"X-API-Key": self.api_key}

        try:
            respuesta = requests.post(self.api_url, json=paquete, headers=headers)
            if respuesta.status_code == 200:
                print(f"Envio exitoso a la nube: {respuesta.json()}")
                return True
            else:
                print(f"Error del servidor nube: {respuesta.status_code}")
                return False
        #Si no hay internet, imprime el aviso y devuelve False
        except(requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            print("Sin conexion a la API de la nube, guardando en cola offline")
            return False

    #Si el paquete llego bien a la nube, borra la tabla sales_now, para no mandar duplicados
    def vaciar_sqlite(self):
        conexion = self.db.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM sales_now")
        conexion.commit()
        conexion.close()
        print("SQLite limpiado tras sincronizacion exitosa")

    #Si no hay internet, convierte el paquete JSON a una linea de texto simple
    def guardar_en_cola(self, paquete):
        linea = json.dumps(paquete)
        with open(self.archivo_cola, "a") as archivo:
            archivo.write(linea + "\n") #La a es de adjuntar al archivo missing-items.txt
        print(f"JSON guardado en cola: {self.archivo_cola}")

    def sincronizacion_nocturna(self):
        """Esto puede ser llamado manualmente si hay un boton en la UI."""
        print("Iniciando sincronizacion...")
        #Tomamos todo lo del SQLite y lo ordenamos en el formato JSON
        paquete = self.empaquetar_ventas()

        if paquete is None:
            return

        envio_exitoso = self.enviar_paquete(paquete)
        if envio_exitoso:
            self.vaciar_sqlite()
        else:
            self.guardar_en_cola(paquete)

    def procesar_cola_pendientes(self):
        #Verificamos si existe el archivo o si el archivo esta vacio
        if not os.path.isfile(self.archivo_cola) or os.stat(self.archivo_cola).st_size == 0:
            return

        #Leemos las lineas
        with open(self.archivo_cola, "r") as archivo:
            lineas = archivo.readlines()

        lineas_pendientes = [] #Creamos esta lista vacia para mandar aqui las lineas que vuelvan a fallar
        conexion_activa = True

        print(f"Intentando reenviar {len(lineas)} paquetes atrasados de la cola...")

        #Procesamos paquete por paquete
        for linea in lineas:
            if not linea.strip(): #Se ignoran saltos de lineas vacios
                continue

            if not conexion_activa:
                lineas_pendientes.append(linea)
                continue

            try:
                paquete = json.loads(linea) #Transformamos el texto a JSON y lo mandamos
                headers = {"X-API-Key": self.api_key}

                respuesta = requests.post(self.api_url, json=paquete, headers=headers)

                if respuesta.status_code == 200:
                    print("Paquete atrasado enviado exitosamente al servidor.")
                else:
                    lineas_pendientes.append(linea)

            except requests.exceptions.RequestException:
                print("La red sigue caida. Pauando el reenvio de la cola.")
                conexion_activa = False
                lineas_pendientes.append(linea)

        with open(self.archivo_cola, "w") as archivo: #Si falla, se abra el mismo archivo en modo escritura, escribiendo unicamente las lineas pendientes
            for linea_pendiente in lineas_pendientes:
                archivo.write(linea_pendiente)


