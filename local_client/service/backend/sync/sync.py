import glob
import json
import os
import time
import threading
import requests
from datetime import datetime
from service.backend.db.sqlite_manager import SQLiteManager

class SyncDaemon:
    """
    Demonio de Sincronizacion en Segundo Plano.
    Garantiza que ninguna venta se pierda si hay caidas de red, gestionando
    empaquetados, reintentos y limpieza de memoria cache temporal.
    """
    def __init__(self, db_manager, api_service, config_manager):
        """
        Constructor del Daemon.
        Prepara las rutas del sistema de archivos y asegura la existencia
        de las carpetas de configuracion y respaldo antes de arrancar.
        """
        self.db = db_manager
        self.api = api_service
        self.config = config_manager

        self.archivo_cola = "missing-items.txt"
        self.archivo_config = "settings.json"

        #Credenciales de la Nube
        self.api_url = "https://bananalytics.onrender.com/api/v1/ventas/sync"
        self.api_key = "Bananalytics-Super-Secret-Key-2026"

        #Mapa del Sistema de Archivos
        self.carpeta_conf = "Conf"
        self.carpeta_data = "data"
        self.carpeta_backup = os.path.join(self.carpeta_data, "Backup")

        self.archivo_config = os.path.join(self.carpeta_conf, "settings.json")
        self.archivo_cola = os.path.join(self.carpeta_data, "missing-items.txt")

        #Autocreacion de estructura de directorios
        os.makedirs(self.carpeta_conf, exist_ok=True)
        os.makedirs(self.carpeta_backup, exist_ok=True)

    def start(self):
        """
        Punto de ignicion.
        Lanza el ciclo de vida del Daemon en un hilo independiente (Thread)
        para mantener la interfaz de usuario completamente fluida.
        """
        hilo = threading.Thread(target=self._ciclo_infinito, daemon=True)
        hilo.start()
        print("Daemon de sincronizacion iniciado en segundo plano")

    #Intenta mandar los archivos atrasados en cola pendientes. Una vez sean las 12, intenta mandar las ventas empaquetadas del dia
    def _ciclo_infinito(self):
        """
        El latido del corazon del sistema.
        Se ejecuta cada 5 segundos evaluando si hay trabajo pendiente
        o si ha llegado la hora estipulada para el cierre de caja.
        """
        time.sleep(5)
        while True:
            self.procesar_cola_pendientes()
            hora_actual = datetime.now().hour
            if True:
                print("Iniciando cierre de caja automatico...")
                self.sincronizacion_nocturna()
                time.sleep(5)

            time.sleep(5)

    #Busca el archivo settings.json para averiguar el ID de la tienda
    def leer_config(self) -> dict:
        """
        Recupera la 'Cedula de Identidad' de la tienda.
        Si por algun motivo critico el archivo se corrompio, genera un default
        para evitar que el sistema colapse.
        """
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
    def empaquetar_ventas(self) -> dict:
        """
        Extrae datos crudos de SQLite y los comprime en bloques de 30 minutos.
        Consolida productos repetidos sumando sus cantidades.
        """
        config = self.leer_config()
        id_store = config.get("store_profile", {}).get("id_store", 1)

        hoy = datetime.now()
        date_str = hoy.strftime("%d-%m-%Y")
        day = hoy.weekday() + 1 #1 = Lunes, 7 = Domingo

        #Extraccion de crudos
        conexion = self.db.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT barcode, time, amount FROM sales_now")
        filas = cursor.fetchall()
        conexion.close()

        if not filas:
            print("No hay ventas locales para empaquetar en SQLite")
            return None #Si no se vendio nada hoy, se aborta

        transacciones = {}
        for fila in filas:
            barcode, hora_venta_completa, amount = fila[0], fila[1], fila[2]

            #Sacamos la hora limpia
            if " " in hora_venta_completa:
                solo_hora = hora_venta_completa.split(" ")[1]
            else:
                solo_hora = hora_venta_completa


            # Separamos "12:45:15" en ["12", "45", "15"]
            partes_tiempo = solo_hora.split(":")
            hora_str = partes_tiempo[0]
            minutos = int(partes_tiempo[1])

            # Redondeamos los minutos hacia abajo
            if minutos < 30:
                bloque_minutos = "00"
            else:
                bloque_minutos = "30"

            # Consolidacion
            llave_bloque = f"{hora_str}:{bloque_minutos}:00"

            # Creamos la cubeta si no existe
            if llave_bloque not in transacciones:
                transacciones[llave_bloque] = {
                    "time": llave_bloque,
                    "products": []
                }

            # Buscamos si ese producto ya está en la cubeta de esta media hora
            lista_productos = transacciones[llave_bloque]["products"]

            # Truco de Python para buscar rápido en una lista de diccionarios
            producto_encontrado = None
            for p in lista_productos:
                if p["barcode"] == barcode:
                    producto_encontrado = p
                    break

            # Si ya existe, le sumamos la cantidad. Si no, lo agregamos nuevo.
            if producto_encontrado:
                producto_encontrado["amount"] += amount
            else:
                lista_productos.append({
                    "barcode": barcode,
                    "amount": amount
                })

        #Estructuracion final para la API
        paquete = {
            "id_store": id_store,
            "date": date_str,
            "day": day,
            "sales": list(transacciones.values())
        }
        return paquete

    #Intenta mandar la caja a la nube
    def enviar_paquete(self, paquete: dict) -> bool:
        """
        Intenta cruzar el puente de red hacia el servidor en la nube.
        Captura excepciones de red sin crashear el sistema.
        """
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

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
        """Purga la base de datos local una vez que los datos estan seguros en Backup o en la Nube"""
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
        """
        Flujo maestro de orquestacion de datos.
        Ejecuta el ciclo: Limpiar Cache -> Empaquetar -> Respaldar Fisico -> Enviar API -> Limpiar SQLite
        """
        print("Iniciando cierre de caja automatico...")

        # 1. Hacemos la limpieza de hace 30 días antes de empezar
        self.limpiar_cache_antiguo()

        # 2. Empaquetamos
        paquete = self.empaquetar_ventas()
        if paquete is None:
            return

        # 3. Extraemos datos para el nombre del archivo
        id_store = paquete.get("id_store", "1")
        date_str = paquete.get("date", datetime.now().strftime("%d-%m-%Y"))

        # 4. SIEMPRE creamos la memoria caché física en /Backup
        nombre_archivo = self.guardar_backup_local(paquete, id_store, date_str)

        # 5. Intentamos enviarlo a la nube
        envio_exitoso = self.enviar_paquete(paquete)

        # 6. Tomamos decisiones
        if envio_exitoso:
            print("Caja en la nube. Todo al corriente.")
        else:
            # Si no hay internet, solo guardamos el NOMBRE en missing-items.txt
            with open(self.archivo_cola, "a") as cola:
                cola.write(nombre_archivo + "\n")
            print(f"📝 Anotado en missing-items.txt para reenvío: {nombre_archivo}")

        # 7. Vaciar SQLite es seguro SIEMPRE, porque el JSON ya está en Backup
        self.vaciar_sqlite()

    def procesar_cola_pendientes(self):
        """
        Lee los nombres de archivos pendientes, los busca en la carpeta de Backup
        y trata de reenviarlos. Actualiza la lista si algunos vuelven a fallar.
        """
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
            nombre_archivo = linea.strip()
            if not nombre_archivo: #Se ignoran saltos de lineas vacios
                continue

            if not conexion_activa:
                lineas_pendientes.append(nombre_archivo + "\n")
                continue

            ruta_archivo = os.path.join(self.carpeta_backup, nombre_archivo)

            if not os.path.exists(ruta_archivo):
                print(f"Archivo: {nombre_archivo} no existe en Backup.")

            try:
                # Extraemos el paquete del archivo guardado
                with open(ruta_archivo, "r") as f:
                    paquete = json.load(f)

                headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}
                respuesta = requests.post(self.api_url, json=paquete, headers=headers)

                if respuesta.status_code == 200:
                    print(f"✅ Paquete atrasado enviado: {nombre_archivo}")
                    # Como se envió, ya no lo agregamos a lineas_pendientes
                else:
                    lineas_pendientes.append(nombre_archivo + "\n")

            except requests.exceptions.RequestException:
                print("La red sigue caída. Pausando el reenvío de la cola.")
                conexion_activa = False
                lineas_pendientes.append(nombre_archivo + "\n")

        # Reescribimos el TXT solo con los nombres que volvieron a fallar
        with open(self.archivo_cola, "w") as archivo:
            for linea in lineas_pendientes:
                archivo.write(linea)

    def guardar_backup_local(self, paquete, id_store, date_str):
        """
        Crea el archivo fisico final en formato JSON para trazabilidad.
        """
        hora_exacta = datetime.now().strftime("%H-%M-%S")

        nombre_archivo = f"{id_store}_{date_str}_{hora_exacta}.json"

        ruta_completa = os.path.join(self.carpeta_backup, nombre_archivo)

        with open(ruta_completa, "w") as archivo:
            json.dump(paquete, archivo, indent=4)

        return nombre_archivo

    def limpiar_cache_antiguo(self):
        """
        Borra cualquier backup que tenga mas de 30 dias de antiguedad
        para evitar llenar el almacenamiento de la computadora local.
        :return:
        """
        dias_limite = 30
        tiempo_actual = time.time()
        archivos_backup = glob.glob(os.path.join(self.carpeta_backup, "*.json"))

        for ruta_archivo in archivos_backup:
            fecha_modificacion = os.path.getmtime(ruta_archivo)
            dias_antiguedad = (tiempo_actual - fecha_modificacion) / (24 * 3600)

            if dias_antiguedad > dias_limite:
                try:
                    os.remove(ruta_archivo)
                    print(f"Cache limpio: {os.path.basename(ruta_archivo)} borrado (mas de 30 dias).")
                except OSError as e:
                    print(f"Error al borrar archivo antiguo: {e}")



