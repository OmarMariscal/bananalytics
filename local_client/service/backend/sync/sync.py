"""
Demonio de Sincronización en Segundo Plano.
Se ejecuta de forma invisible para agrupar ventas locales y enviarlas a la nube.
Diseñado para ser resiliente: si no hay red, guarda los paquetes y reintenta después.
"""

import glob
import json
import os
import time
import threading
from datetime import datetime


class SyncDaemon:
    def __init__(self, db_manager, api_service, config_manager):
        self.db = db_manager
        self.api = api_service
        self.config = config_manager

        # Carpetas para manejar la cola de envíos y respaldos de seguridad
        self.carpeta_data = "data"
        self.carpeta_conf = os.path.join(self.carpeta_data, "Conf")
        self.carpeta_backup = os.path.join(self.carpeta_data, "Backup")

        self.archivo_config = os.path.join(self.carpeta_conf, "settings.json")
        self.archivo_cola = os.path.join(self.carpeta_data, "missing-items.txt")

        # Bandera en memoria para evitar doble sincronización en un mismo día
        self._fecha_ultima_sync = None

        os.makedirs(self.carpeta_conf, exist_ok=True)
        os.makedirs(self.carpeta_backup, exist_ok=True)

    def start(self):
        """Inicia el demonio en un hilo separado para no bloquear la Interfaz de Usuario."""
        hilo = threading.Thread(target=self._ciclo_infinito, daemon=True)
        hilo.start()
        print("[SyncDaemon] Daemon de sincronizacion iniciado en segundo plano.")

    def _ciclo_infinito(self):
        """
        Latido principal del daemon. Se ejecuta cada 60 segundos buscando sus ventanas horarias.
        Al arrancar, intenta limpiar la cola de pendientes por si la app estuvo apagada.
        """
        print("[SyncDaemon] Verificando cola de pendientes al arrancar...")
        try:
            self.procesar_cola_pendientes()
        except Exception as e:
            print(f"[SyncDaemon] Error en recuperación al arranque: {e}")

        while True:
            try:
                ahora = datetime.now()
                hoy = ahora.date()
                ya_sincronize_hoy = (self._fecha_ultima_sync == hoy)

                # Ventana principal: Medianoche (00:00 a 00:09)
                en_ventana_principal = (ahora.hour == 0 and ahora.minute < 10)

                if en_ventana_principal and not ya_sincronize_hoy:
                    self.sincronizacion_nocturna()
                    self._fecha_ultima_sync = hoy
                    print(f"[SyncDaemon] Cierre de caja completado para {hoy}.")

                # Ventana de respaldo (01:00 a 01:29) por si la PC estaba apagada a medianoche
                en_ventana_barrido = (ahora.hour == 1 and ahora.minute < 30)

                if en_ventana_barrido and not ya_sincronize_hoy:
                    self.sincronizacion_nocturna()
                    self._fecha_ultima_sync = hoy
                    print(f"[SyncDaemon] Cierre de respaldo completado para {hoy}.")

            except Exception as e:
                print(f"[SyncDaemon] Error en ciclo principal, continuando: {e}")

            time.sleep(60)

    def empaquetar_ventas(self) -> dict:
        """Agrupa las ventas crudas de SQLite en bloques de 30 minutos."""
        id_store = int(self.config.get_store_id())

        conexion = self.db.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT time FROM sales_now ORDER BY time ASC LIMIT 1")
        primer_registro = cursor.fetchone()

        if not primer_registro:
            conexion.close()
            return None

        tiempo_completo = primer_registro[0]
        fecha_filtro = tiempo_completo.split(" ")[0] if " " in tiempo_completo else datetime.now().strftime("%Y-%m-%d")

        cursor.execute(
            "SELECT barcode, time, amount FROM sales_now WHERE time LIKE ?",
            (f"{fecha_filtro}%",)
        )
        filas = cursor.fetchall()
        conexion.close()

        # Determinar día y fecha para el payload
        try:
            fecha_obj = datetime.strptime(fecha_filtro, "%Y-%m-%d")
            date_str = fecha_obj.strftime("%d-%m-%Y")
            day = fecha_obj.weekday() + 1
        except ValueError:
            fecha_obj = datetime.now()
            date_str = fecha_obj.strftime("%d-%m-%Y")
            day = fecha_obj.weekday() + 1

        transacciones = {}
        for fila in filas:
            barcode, hora_venta_completa, amount = fila[0], fila[1], fila[2]

            solo_hora = hora_venta_completa.split(" ")[1] if " " in hora_venta_completa else hora_venta_completa
            partes_tiempo = solo_hora.split(":")
            hora_str = partes_tiempo[0]
            minutos = int(partes_tiempo[1])

            # Lógica de agrupamiento en bloques de media hora
            bloque_minutos = "00" if minutos < 30 else "30"
            llave_bloque = f"{hora_str}:{bloque_minutos}:00"

            if llave_bloque not in transacciones:
                transacciones[llave_bloque] = {"time": llave_bloque, "products": []}

            lista_productos = transacciones[llave_bloque]["products"]
            producto_encontrado = next((p for p in lista_productos if p["barcode"] == barcode), None)

            if producto_encontrado:
                producto_encontrado["amount"] += amount
            else:
                lista_productos.append({"barcode": barcode, "amount": amount})

        paquete = {
            "id_store": id_store,
            "date": date_str,
            "day": day,
            "sales": list(transacciones.values()),
            "_fecha_db": fecha_filtro  # Bandera interna para saber qué borrar después
        }
        return paquete

    def enviar_paquete(self, paquete: dict) -> bool:
        """Delega el envío al ApiClient usando el JWT almacenado."""
        token = self.config.get_jwt_token()
        return self.api.sync_sales(paquete, token)

    def vaciar_sqlite(self, fecha_procesada: str = None):
        """Purga la base local de aquellas ventas que ya se mandaron a la nube."""
        conexion = self.db.obtener_conexion()
        cursor = conexion.cursor()
        if fecha_procesada:
            cursor.execute("DELETE FROM sales_now WHERE time LIKE ?", (f"{fecha_procesada}%",))
        else:
            cursor.execute("DELETE FROM sales_now")
        conexion.commit()
        conexion.close()

    def sincronizacion_nocturna(self):
        """Flujo de orquestación de fin de día."""
        print("[SyncDaemon] Iniciando cierre de caja automatico...")
        self.limpiar_cache_antiguo()

        paquete = self.empaquetar_ventas()
        if paquete is None:
            return

        id_store = paquete.get("id_store", "1")
        date_str = paquete.get("date", datetime.now().strftime("%d-%m-%Y"))

        # Extraemos la bandera interna antes de guardar el JSON o enviarlo
        fecha_db_exacta = paquete.pop("_fecha_db", None)

        nombre_archivo = self.guardar_backup_local(paquete, id_store, date_str)
        envio_exitoso = self.enviar_paquete(paquete)

        if envio_exitoso:
            print(f"[SyncDaemon] Caja del día {date_str} asegurada en la nube.")
        else:
            # Si no hay internet, anotamos el archivo en la cola para reintentar mañana
            with open(self.archivo_cola, "a") as cola:
                cola.write(nombre_archivo + "\n")
            print(f"[SyncDaemon] Anotado en missing-items.txt para reenvío: {nombre_archivo}")

        self.vaciar_sqlite(fecha_procesada=fecha_db_exacta)

    def procesar_cola_pendientes(self):
        """Lee el archivo de cola e intenta mandar a la API todo lo rezagado."""
        if not os.path.isfile(self.archivo_cola) or os.stat(self.archivo_cola).st_size == 0:
            return

        with open(self.archivo_cola, "r") as archivo:
            lineas = archivo.readlines()

        lineas_pendientes = []
        conexion_activa = True
        token = self.config.get_jwt_token()

        for linea in lineas:
            nombre_archivo = linea.strip()
            if not nombre_archivo: continue

            # Si la red falló en este ciclo, paramos y guardamos el resto
            if not conexion_activa:
                lineas_pendientes.append(nombre_archivo + "\n")
                continue

            ruta_archivo = os.path.join(self.carpeta_backup, nombre_archivo)
            if not os.path.exists(ruta_archivo):
                continue

            try:
                with open(ruta_archivo, "r") as f:
                    paquete = json.load(f)

                if self.api.sync_sales(paquete, token):
                    print(f"[SyncDaemon] ✅ Paquete atrasado enviado: {nombre_archivo}")
                else:
                    lineas_pendientes.append(nombre_archivo + "\n")

            except json.JSONDecodeError:
                print(f"[SyncDaemon] Archivo corrupto, descartando: {nombre_archivo}")
                continue
            except Exception as e:
                print(f"[SyncDaemon] Error de red, pausando reenvíos. Motivo: {e}")
                conexion_activa = False
                lineas_pendientes.append(nombre_archivo + "\n")

        with open(self.archivo_cola, "w") as archivo:
            for linea in lineas_pendientes:
                archivo.write(linea)

    def guardar_backup_local(self, paquete: dict, id_store: str, date_str: str) -> str:
        """Crea un respaldo de las transacciones diarias en formato JSON."""
        hora_exacta = datetime.now().strftime("%H-%M-%S")
        nombre_archivo = f"{id_store}_{date_str}_{hora_exacta}.json"
        ruta_completa = os.path.join(self.carpeta_backup, nombre_archivo)
        with open(ruta_completa, "w") as archivo:
            json.dump(paquete, archivo, indent=4)
        return nombre_archivo

    def limpiar_cache_antiguo(self):
        """Política de retención: borra respaldos de más de 30 días para ahorrar espacio."""
        dias_limite = 30
        tiempo_actual = time.time()
        archivos_backup = glob.glob(os.path.join(self.carpeta_backup, "*.json"))

        for ruta_archivo in archivos_backup:
            fecha_modificacion = os.path.getmtime(ruta_archivo)
            dias_antiguedad = (tiempo_actual - fecha_modificacion) / (24 * 3600)
            if dias_antiguedad > dias_limite:
                try:
                    os.remove(ruta_archivo)
                except OSError:
                    pass