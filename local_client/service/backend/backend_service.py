"""
Fachada Principal de la Aplicación.
Orquesta y conecta la UI (Frontend), la Nube (API), la BD local y los eventos
de hardware (Scanner). El Frontend solo necesita hablar con esta clase.
"""

import os
import base64
import threading
from datetime import datetime, date, timedelta

from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User
from service.backend.db.sqlite_manager import SQLiteManager
from service.backend.sync.sync import SyncDaemon
from service.backend.config.config_manager import ConfigManager
from service.backend.peticiones_api import ApiClient
from service.backend.scanner_listener import ScannerListener
from service.backend.notification_manager import NotificationManager


class BackendService:
    def __init__(self):
        # Instanciar todos los módulos secundarios
        self.db = SQLiteManager()
        self.config = ConfigManager()
        self.api = ApiClient()
        self.notifier = NotificationManager()
        self.daemon = SyncDaemon(self.db, self.api, self.config)
        self.vigilante = ScannerListener(backend_service=self)

        # Iniciar hilos de fondo solo si el usuario ya está registrado
        if not self.config.is_first_start():
            hilo_fantasma = threading.Thread(target=self.daemon._ciclo_infinito)
            hilo_fantasma.daemon = True
            hilo_fantasma.start()
            self.vigilante.iniciar()
            print("[BackendService] Motor iniciado.")
        else:
            print("[BackendService] Esperando registro inicial.")

    def sync(self) -> bool:
        """Flujo maestro invocado manualmente desde el botón de 'Sincronizar' en la UI."""
        if not self.api.check_health():
            return False

        try:
            self.daemon.procesar_cola_pendientes()

            # Descargamos predicciones solo 1 vez y las pasamos a los demás métodos
            # para ahorrar datos de red en conexiones lentas.
            predicciones_frescas = self.get_alerts()
            self.get_dashboard_stats(alertas_precargadas=predicciones_frescas)
            self.check_and_build_report()
            return True
        except Exception as e:
            print(f"[BackendService] Error inesperado durante sync: {e}")
            return False

    def get_alerts(self) -> list[PredictionAlert]:
        """Solicita las predicciones a la API y las formatea para las tarjetas de la UI."""
        token = self.config.get_jwt_token()
        store_id = self.config.get_store_id()

        caja_dashboard = self.api.get_dashboard_data(store_id, token)

        # Tolerancia a fallos: Si no hay red, cargamos la caché local
        if caja_dashboard:
            self.config.save_last_dashboard(caja_dashboard)
        else:
            caja_dashboard = self.config.get_last_dashboard()

        alertas_formateadas = []
        for alerta in caja_dashboard.get("predictions", []):
            fecha_texto = alerta.get("objective_date", alerta.get("objetive_date", "2026-04-10"))
            try:
                fecha_obj = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
            except ValueError:
                fecha_obj = date.today()

            nueva_alerta = PredictionAlert(
                product_name=alerta.get("product_name", alerta.get("name", "Desconocido")),
                barcode=alerta.get("barcode", "000000"),
                category=alerta.get("category", alerta.get("Category", "General")),
                image_url=alerta.get("image_url", "https://via.placeholder.com/150"),
                objective_date=fecha_obj,
                prediction=alerta.get("prediction", 0),
                avg_weekly_sales=alerta.get("avg_weekly_sales", 0),
                type=alerta.get("type", "neutral"),
                feature=alerta.get("feature", False),
                percentage_average_deviation=alerta.get("percentage_average_deviation", 0.0),
                margin_of_error=alerta.get("margin_of_error", 0),
            )
            alertas_formateadas.append(nueva_alerta)

        return alertas_formateadas

    def get_product_detail(self, barcode: str) -> PredictionAlert:
        """Busca los detalles predictivos específicos de un solo producto."""
        token = self.config.get_jwt_token()
        store_id = self.config.get_store_id()

        caja_dashboard = self.api.get_dashboard_data(store_id, token)
        detalle = next((p for p in caja_dashboard.get("predictions", []) if p.get("barcode") == barcode), None)

        if detalle is None:
            return PredictionAlert(barcode=barcode)

        fecha_texto = detalle.get("objective_date", detalle.get("objetive_date", ""))
        try:
            fecha_obj = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
        except ValueError:
            fecha_obj = date.today()

        return PredictionAlert(
            product_name=detalle.get("product_name", "Desconocido"),
            barcode=barcode,
            category=detalle.get("category", "General"),
            image_url=detalle.get("image_url", ""),
            objective_date=fecha_obj,
            prediction=detalle.get("prediction", 0),
            avg_weekly_sales=detalle.get("avg_weekly_sales", 0.0),
            type=detalle.get("type", "neutral"),
            feature=detalle.get("feature", False),
            percentage_average_deviation=detalle.get("percentage_average_deviation", 0.0),
            margin_of_error=detalle.get("margin_of_error", 0),
        )

    def get_dashboard_stats(self, alertas_precargadas: list[PredictionAlert] | None = None) -> dict:
        """Construye los números rápidos para la parte superior del Dashboard."""
        stats_db = self.db.get_today_stats()

        pendientes = 0
        if os.path.exists(self.daemon.archivo_cola):
            with open(self.daemon.archivo_cola, "r") as f:
                pendientes = sum(1 for linea in f if linea.strip())

        alertas = alertas_precargadas if alertas_precargadas is not None else self.get_alerts()

        return {
            "total_scans_today": stats_db["total_scans_today"],
            "active_predictions": len(alertas),
            "pending_syncs": pendientes,
            "is_online": self.api.check_health()
        }

    def get_dashboard_details(self) -> dict:
        """Devuelve los datos crudos para pintar las gráficas del UI."""
        token = self.config.get_jwt_token()
        store_id = self.config.get_store_id()
        caja_dashboard = self.api.get_dashboard_data(store_id, token)
        return caja_dashboard.get("weekly_summary", {"labels": [], "actual_sales": [], "predicted_sales": []})

    def is_first_start(self) -> bool:
        return self.config.is_first_start()

    def register_user(self, user: User) -> dict:
        """
        Gestiona el flujo de registro en la Nube y la configuración local.
        {'status': bool, 'message': str}
        """
        ubicacion = self.config._obtener_ubicacion_por_ip()
        respuesta_api = self.api.register_user(user, ubicacion)

        estado = respuesta_api.get("status")
        # Obtenemos el mensaje de la API de Ángel
        mensaje_api = respuesta_api.get("mensaje", "Error desconocido.")

        if estado == "exito":
            self.config.create_configurations(user, respuesta_api["id_negocio"], respuesta_api["token"])

            # Una vez registrados, despertamos los demonios de hardware y red
            hilo_fantasma = threading.Thread(target=self.daemon._ciclo_infinito)
            hilo_fantasma.daemon = True
            hilo_fantasma.start()
            self.vigilante.iniciar()

            # Estructura que espera el frontend para el éxito
            return {
                "status": True,
                "message": "El correo ha sido registrado"
            }

        # Estructura que espera el frontend para el error
        return {
            "status": False,
            "message": mensaje_api
        }

    def get_sales_history(self, barcode: str) -> list[dict]:
        """Formatea el historial de un producto para la gráfica individual."""
        token = self.config.get_jwt_token()
        store_id = self.config.get_store_id()
        caja_producto = self.api.get_product_data(store_id, barcode, token)
        historial_bruto = caja_producto.get("history", [])

        if isinstance(historial_bruto, list):
            lista_formateada = []
            for item in historial_bruto:
                if isinstance(item, dict):
                    fecha = item.get("date", item.get("fecha", ""))
                    volumen = item.get("volume", item.get("total vendido", item.get("total_vendido", 0)))
                    lista_formateada.append({"date": fecha, "volume": volumen})
            return lista_formateada
        return []

    def get_app_stats(self) -> ConfigStats:
        return self.config.get_app_stats()

    def get_server_status(self) -> bool:
        return self.api.check_health()

    def registrar_venta(self, codigo_barras: str) -> bool:
        """Filtro principal para las pulsaciones del escáner físico."""
        try:
            codigo_limpio = codigo_barras.strip()

            if not self._es_codigo_valido(codigo_limpio):
                return False

            return self.db.guardar_venta_local(codigo_limpio)
        except Exception:
            return False

    def _es_codigo_valido(self, codigo: str) -> bool:
        """Regla de Negocio: Solo permitimos formatos estándares comerciales EAN y UPC."""
        codigo_limpio = codigo.strip()
        longitudes_validas = (8, 12, 13)
        return len(codigo_limpio) in longitudes_validas and codigo_limpio.isdigit()

    def check_and_build_report(self):
        """Descarga el PDF del reporte semanal si han pasado 7 días."""
        hoy = date.today()
        fecha_ultimo_reporte = self.config.get_last_report_date()

        if (hoy - fecha_ultimo_reporte).days < 7:
            return

        datos_app = self.get_app_stats()
        username = datos_app.user_name.replace(" ", "_") if datos_app else "Usuario"

        token = self.config.get_jwt_token()
        respuesta = self.api.get_weekly_report(self.config.get_store_id(), token)
        binario_base64 = respuesta.get("response")

        if not binario_base64:
            return

        try:
            ruta_carpeta = os.path.join("data", "reports")
            os.makedirs(ruta_carpeta, exist_ok=True)
            nombre_archivo = f"BanAnalytics_Report_{username}_{hoy.strftime('%Y_%m_%d')}.pdf"
            ruta_final = os.path.join(ruta_carpeta, nombre_archivo)

            # Decodificamos el Base64 a un binario PDF real
            with open(ruta_final, "wb") as f:
                f.write(base64.b64decode(binario_base64))

            # Cálculos de fechas para la ventana de la notificación visual
            lunes_actual = hoy - timedelta(days=hoy.weekday())
            domingo_cierre = lunes_actual - timedelta(days=1)
            lunes_inicio = lunes_actual - timedelta(days=7)

            self.config.update_last_report_date(lunes_actual)

            # Lanzamos la alerta visual de Windows
            self.notifier.notify_new_report(ruta_final, lunes_inicio, domingo_cierre)
            print("La cosa llegó, pa")
        except Exception as e:
            print(f"[BackendService] Error construyendo el PDF: {e}")