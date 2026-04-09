from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User
from service.backend.db.sqlite_manager import SQLiteManager
from service.backend.sync.sync import SyncDaemon
from service.backend.config.config_manager import ConfigManager
from local_client.service.backend.peticiones_api import ApiClient
from datetime import datetime, date

class BackendService: #Activa todas las herramientas, si no es primer inicio, arranca el daemon
    def __init__(self):
        self.db = SQLiteManager()
        self.config = ConfigManager()
        self.api = ApiClient()
        self.daemon = SyncDaemon(self.db)

        if not self.config.is_first_start():
            self.daemon.start()

    #Metodo privado del backend
    #Sirve para auxiliar a otros metodos
    def _get_store_id(self) -> str:
        import json
        try:
            with open(self.config.archivo_config, "r") as f:
                config = json.load(f)
                return str(config.get("store_profile", {}).get("store_id", "1"))
        except:
            return "1"

    #Se le pide a la api los datos del dashboard y de ellos, solo se seleccionan las alertas
    #Se extraen los datos crudos y se transforman en objetos Python,
    #Se devuelve una lista de estos objetos
    def get_alerts(self) -> list[PredictionAlert]:
        caja_dashboard = self.api.get_dashboard_data(self._get_store_id())
        alertas_brutas = caja_dashboard.get("alerts", [])

        alertas_formateadas = []
        for alerta in alertas_brutas:

            fecha_texto = alerta.get("objective_date", "2026-04-10")
            try:
                fecha_obj = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
            except ValueError:
                fecha_obj = date.today()

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
        stats_db = self.db.get_today_stats()

        import os
        pendientes = 0
        if os.path.exists("missing-items.txt"):
            with open("missing-items.txt", "r") as f:
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
        caja_dashboard = self.api.get_dashboard_data(self._get_store_id())
        return caja_dashboard.get("weekly_summary", {"labels": [], "actual_sales": [], "predicted_sales": []})

    #La validación debe ser con un archivo creado con el método create_configurations
    #Busca en el config manager, con un True o False Flet decidira si manda la pantalla de registro o al dashboard
    def is_first_start(self) -> bool:
        return self.config.is_first_start()

    #Se manda el usuario registrado a las peticiones api, y se ordena crear el JSON y arranca el Daemon
    #Se regresa el diccionario con el status
    def register_user(self, user: User) -> dict:
        respuesta_api = self.api.register_user(user)

        if respuesta_api["status"] == "exito":
            self.config.create_configurations(user, respuesta_api["id_negocio"])
            self.daemon.start()

        return respuesta_api

    #Saca el historial del producto
    #Se devuelve una lista de diccionarios. Flet usara los puntos X y Y para dibujar la linea ondulada de ventas en la parte inferior de la pantalla del producto
    def get_sales_history(self, barcode: str) -> list[dict]:
        caja_producto = self.api.get_product_data(self._get_store_id(), barcode)
        historial_bruto = caja_producto.get("history", [])

        if isinstance(historial_bruto, list):
            return historial_bruto

        if isinstance(historial_bruto, dict):
            fechas = historial_bruto.get("fechas", [])
            ventas = historial_bruto.get("ventas", [])

            lista_formateada = [{"date": f, "volume": v} for f, v in zip(fechas, ventas)]
            return lista_formateada
        return []

    #Se pide el perfil al config_manager, se devuelve un objeto ConfigStats
    def get_app_stats(self) -> ConfigStats:
        return self.config.get_app_stats()

    
    def get_server_status(self) -> bool:
        return True
