import threading
from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User
from service.backend.db.sqlite_manager import SQLiteManager
from service.backend.sync.sync import SyncDaemon
from service.backend.config.config_manager import ConfigManager
from local_client.service.backend.peticiones_api import ApiClient
from datetime import datetime, date
from local_client.service.backend.scanner_listener import ScannerListener
from shared.utils.validators import Validators
import os


class BackendService: #Activa todas las herramientas, si no es primer inicio, arranca el daemon
    """
    Punto unico de contacto entre la Interfaz Grafica y la logica de negocio.
    Controla el ciclo de vida del Hardware, la Nube y el almacenamiento local.
    """
    def __init__(self):
        """
        Inicializa y ensambla todos los submotores del sistema.
        Evalua si la tienda ya esta configurada para despertar los servicios en segundo plano
        """
        self.db = SQLiteManager()
        self.config = ConfigManager()
        self.api = ApiClient()

        self.daemon = SyncDaemon(
            db_manager=self.db,
            api_service=self.api,
            config_manager=self.config
        )

        self.vigilante = ScannerListener(backend_service=self)
        self.vigilante.iniciar()

        if not self.config.is_first_start():
            hilo_fantasma = threading.Thread(target=self.daemon._ciclo_infinito)
            hilo_fantasma.daemon = True
            hilo_fantasma.start()
            print("BackendService: Motor iniciado y SyncDaemon corriendo en segundo plano.")
        else:
            print("BackendService: Primer inicio, esperando a que usuario se registre...")

    def sync(self) -> bool:
        print("[BackendService] Se ha solicitado sincronizacion manual...")
        if not self.api.check_health():
            print("[BackendService] Sincronizacion abortada: Servidor no disponible.")
            return False

        print("[BckendService] Servidor en linea. Empaquetando y enviando datos...")

        try:
            self.daemon.procesar_cola_pendientes()
            print("[BackendService] Sincronizacion completada. Predicciones actualizadas.")
            return True
        except Exception as e:
            print(f"[BckendService] Error inesperado durante la sincronizacion: {e}")
            return False

    #Metodo privado del backend
    #Sirve para auxiliar a otros metodos
    def _get_store_id(self) -> str:
        """
        Metodo Privado.
        Lee rapidamente el archivo de configuracion para obtener el ID de la sucursal actual.
        Si hay un fallo de lectura, devuelve un '1' como salvavidas.
        """
        import json
        try:
            with open(self.config.archivo_config, "r") as f:
                config = json.load(f)
                return str(config.get("store_profile", {}).get("id_store", "1"))
        except:
            return "1"


    #Se le pide a la api los datos del dashboard y de ellos, solo se seleccionan las alertas
    #Se extraen los datos crudos y se transforman en objetos Python,
    #Se devuelve una lista de estos objetos
    def get_alerts(self) -> list[PredictionAlert]:
        """
        Alimenta las notificaciones y la lista principal de Flet
        Filtra el JSON que manda Angel y lo convierte en objetos Python manejables

        Returns:
            list[PredictionAlert]: Lista de modelos de alerta validados.

        """
        caja_dashboard = self.api.get_dashboard_data(self._get_store_id())
        alertas_brutas = caja_dashboard.get("predictions", [])

        alertas_formateadas = []
        for alerta in alertas_brutas:
            #Transformacion de fechas
            fecha_texto = alerta.get("objective_date", "2026-04-10")
            try:
                fecha_obj = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
            except ValueError:
                fecha_obj = date.today()

            #Mapeo de DTO al Modelo de Dominio
            nueva_alerta = PredictionAlert(
                product_name=alerta.get("name", "Producto Desconocido"),
                barcode=alerta.get("barcode", "000000"),
                category=alerta.get("category", "General"),
                image_url=alerta.get("image_url", "https://via.placeholder.com/150"),
                objective_date=fecha_obj,
                prediction=alerta.get("prediction", 0),
                avg_weekly_sales=alerta.get("avg_weekly_sales", 0.0),
                type=alerta.get("type", "neutral"),
                feature=alerta.get("feature", False)
            )
            alertas_formateadas.append(nueva_alerta)
        return alertas_formateadas

    #Se le pide a la API la info de algun producto en especifico
    #Inyectamos imagenes por defecto si Angel no manda ninguna
    def get_product_detail(self, barcode: str) -> PredictionAlert:
        """
        Extrae los detalles completos de un solo producto.
        Inyecta placeholders visuales si el servidor no devuelve imagenes.
        """
        caja_producto = self.api.get_product_data(self._get_store_id(), barcode)
        detalle = caja_producto.get("detail", {})

        fecha_texto = detalle.get("objective_date", "2026-04-10")
        try:
            fecha_obj = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
        except ValueError:
            fecha_obj = date.today()

        return PredictionAlert(
            product_name=detalle.get("name", "Producto Desconocido"),
            barcode=barcode,
            category=detalle.get("category", "General"),
            image_url=detalle.get("image_url", "https://via.placeholder.com/150"),
            objective_date=fecha_obj,
            prediction=detalle.get("prediction", 0),
            avg_weekly_sales=detalle.get("avg_weekly_sales", 0.0),
            type=detalle.get("type", "neutral"),
            feature=detalle.get("feature", False)
        )

    #Mezcla el total de escaneos de SQLite con el conteo de lineas de missing-items.txt
    #Se regresa un diccionario con 4 llaves exactas
    def get_dashboard_stats(self) -> dict:
        """
        Genera el resumen matematico para las tarjetas superiores del Dashboard.
        Combina datos del SQLite con el sistema de archivos (ventas atoradas).
        """
        stats_db = self.db.get_today_stats()

        pendientes = 0
        if os.path.exists(self.daemon.archivo_cola):
            with open(self.daemon.archivo_cola, "r") as f:
                pendientes = len(f.readlines())

        return {
            "total_scans_today": stats_db["total_scans_today"],
            "active_predictions": 0,
            "pending_syncs": pendientes,
            "is_online": True
        }

    #Grafica Central del dashboard
    #Se devuelve el diccionario con listas adentro
    #Funcion faltante en el Mock
    def get_dashboard_details(self) -> dict:
        """
        Alimenta la grafica central de barras/lineas del Dashboard.
        Devuelve listas separadas para los ejes X (labels) y Y (datos).
        """
        caja_dashboard = self.api.get_dashboard_data(self._get_store_id())
        return caja_dashboard.get("weekly_summary", {"labels": [], "actual_sales": [], "predicted_sales": []})

    #La validación debe ser con un archivo creado con el método create_configurations
    #Busca en el config manager, con un True o False Flet decidira si manda la pantalla de registro o al dashboard
    def is_first_start(self) -> bool:
        """
        Le indica a la UI si debe mostrar el Login o saltar directo al Dashboard.
        """
        return self.config.is_first_start()

    #Se manda el usuario registrado a las peticiones api, y se ordena crear el JSON y arranca el Daemon
    #Se regresa el diccionario con el status
    def register_user(self, user: User) -> dict:
        """
        Flujo de onboarding de nueva sucursal.
        Aplica el Regex, registra en la nube y libera al Daemon
        """
        #Validar antes de ir a la red
        if not Validators.es_correo_valido(user.email):
            return {"status": "fail", "message": "El formato del correo es invalido."}
        respuesta_api = self.api.register_user(user)

        if respuesta_api["status"] == "exito":
            self.config.create_configurations(user, respuesta_api["id_negocio"])

            self.daemon.start()

            print("[Backend] Primer registro exitoso.")
        return respuesta_api

    #Saca el historial del producto
    #Se devuelve una lista de diccionarios. Flet usara los puntos X y Y para dibujar la linea ondulada de ventas en la parte inferior de la pantalla del producto
    def get_sales_history(self, barcode: str) -> list[dict]:
        """
        Obtiene los puntos del plano cartesiano (X, Y) para dibujar
        la grafica ondulada de rendimiento de un producto especifico.
        """
        caja_producto = self.api.get_product_data(self._get_store_id(), barcode)
        historial_bruto = caja_producto.get("history", [])

        #Si la API ya lo manda como lista de diccionarios, lo pasamos directo
        if isinstance(historial_bruto, list):
            return historial_bruto

        #Si Angel lo manda como dos listas separadas, las unimos con zip
        if isinstance(historial_bruto, dict):
            fechas = historial_bruto.get("fechas", [])
            ventas = historial_bruto.get("ventas", [])

            lista_formateada = [{"date": f, "volume": v} for f, v in zip(fechas, ventas)]
            return lista_formateada
        return []

    #Se pide el perfil al config_manager, se devuelve un objeto ConfigStats
    def get_app_stats(self) -> ConfigStats:
        """Recupera metadatos del sistema."""
        return self.config.get_app_stats()

    
    def get_server_status(self) -> bool:
        """Hace un 'ping' rapido para saber si el internet y la nube estan vivos."""
        return True #Temporal, recordar cambiar

    def registrar_venta(self, codigo_barras: str) -> bool:
        """
        Puente directo entre el Hardware y la base de datos SQLite.
        Filtra escaneos fantasmas o vacios.
        """
        try:
            codigo_limpio = codigo_barras.strip()

            if not codigo_limpio:
                print("[BackendService] Se intento registrar un codigo vacio.")
                return False
            print(f"[BackendService] Procesando codigo atrapado: {codigo_limpio}")

            exito = self.db.guardar_venta_local(codigo_limpio)

            if exito:
                print("[BackendService] Venta asegurada en SQLite.")
                return True
            else:
                print("[BackendService] Error interno de la base de datos al guardar.")
                return False
        except Exception as e:
            print(f"[BackendService] Excepcion critica al registrar venta: {e}")
            return False
