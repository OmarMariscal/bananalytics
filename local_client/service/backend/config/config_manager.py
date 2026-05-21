"""
Administrador de Configuraciones Locales.
Maneja el estado persistente de la aplicación en el disco duro (settings.json).
Decide si la aplicación debe comportarse como nueva o si ya tiene
una identidad confirmada por la nube.
"""

import os
import json
import requests
from requests.exceptions import RequestException
from datetime import date, datetime, timedelta

from shared.models.user import User
from shared.models.info_config import ConfigStats


class ConfigManager:
    def __init__(self):
        # Define la estructura de carpetas locales donde se guardarán los datos
        self.carpeta_data = "data"
        self.carpeta_conf = os.path.join(self.carpeta_data, "Conf")
        os.makedirs(self.carpeta_conf, exist_ok=True)

        self.archivo_config = os.path.join(self.carpeta_conf, "settings.json")
        self.archivo_cache_dashboard = os.path.join(self.carpeta_conf, "last_dashboard.json")

    def is_first_start(self) -> bool:
        """
        El Gatekeeper de la Interfaz.
        El frontend (Flet) llama a este método para decidir si muestra la pantalla de
        Registro Inicial o si pasa directamente al Dashboard.
        """
        if not os.path.exists(self.archivo_config):
            return True
        try:
            with open(self.archivo_config, "r") as f:
                config = json.load(f)
                return not config.get("system", {}).get("first_launch_completed", False)
        except (json.JSONDecodeError, KeyError):
            return True

    def _obtener_ubicacion_por_ip(self) -> dict:
        """
        Detecta la ubicación aproximada de la tienda usando su IP pública.
        Se usa durante el registro para enviarle esta data a la API.
        """
        url = "http://ip-api.com/json/"
        try:
            respuesta = requests.get(url, timeout=5)
            respuesta.raise_for_status()
            datos = respuesta.json()

            if datos.get("status") == "success":
                return {
                    "ip": datos.get("query"),
                    "pais": datos.get("country"),
                    "ciudad": f"{datos.get('city')}, {datos.get('regionName')}",
                    "latitud": datos.get("lat"),
                    "longitud": datos.get("lon"),
                    "isp": datos.get("isp")
                }
            return {}
        except RequestException as e:
            print(f"[ConfigManager] Error de red al detectar ubicacion: {e}")
            return {}

    def create_configurations(self, user: User, id_store: str, token: str) -> bool:
        """
        Genera la "Cédula de Identidad" de la tienda (settings.json).
        Solo se ejecuta después de que la API aprueba el registro inicial.
        Guarda el JWT, el ID de tienda y la ubicación.
        """
        print("[ConfigManager] Detectando ubicación geográfica...")
        ubicacion_detectada = self._obtener_ubicacion_por_ip()

        hoy = date.today()
        # Establecemos el control de reportes al lunes de esta semana
        lunes_inicial = hoy - timedelta(days=hoy.weekday())

        config_data = {
            "system": {
                "first_launch_completed": True,
                "local_db_path": "./tienda.db",
                "last_report_date": lunes_inicial.strftime("%Y-%m-%d"),
                "jwt_token": str(token)
            },
            "store_profile": {
                "id_store": str(id_store),
                "owner_name": user.name,
                "email": user.email,
                "location": {
                    "city": ubicacion_detectada.get("ciudad", "Guadalajara, Jalisco"),
                    "lat": ubicacion_detectada.get("latitud", 20.6596),
                    "lng": ubicacion_detectada.get("longitud", -103.3496)
                }
            }
        }

        try:
            with open(self.archivo_config, "w") as f:
                json.dump(config_data, f, indent=4)
            return True
        except Exception as e:
            print(f"[ConfigManager] Error al escribir configuraciones: {e}")
            return False

    def get_jwt_token(self) -> str:
        """Punto único de acceso al Token JWT para firmar las peticiones HTTP."""
        if not os.path.exists(self.archivo_config):
            return ""
        try:
            with open(self.archivo_config, "r") as f:
                return json.load(f).get("system", {}).get("jwt_token", "")
        except (json.JSONDecodeError, KeyError):
            return ""

    def get_store_id(self) -> str:
        """Recupera el identificador único de la tienda asignado por la nube."""
        if not os.path.exists(self.archivo_config):
            return "1"
        try:
            with open(self.archivo_config, "r") as f:
                return str(json.load(f).get("store_profile", {}).get("id_store", "1"))
        except (json.JSONDecodeError, KeyError):
            return "1"

    def get_app_stats(self) -> ConfigStats:
        """Provee los datos básicos del usuario para pintar la barra lateral de la UI."""
        if self.is_first_start():
            return None
        try:
            with open(self.archivo_config, "r") as f:
                perfil = json.load(f).get("store_profile", {})
                return ConfigStats(
                    user_name=perfil.get("owner_name", "Usuario"),
                    email=perfil.get("email", ""),
                    theme_mode=True,
                    current_date=date.today()
                )
        except Exception as e:
            print(f"[ConfigManager] Error al leer perfil de usuario: {e}")
            return None

    def get_last_report_date(self) -> date:
        """Controla cuándo fue la última vez que se generó un reporte semanal PDF."""
        try:
            with open(self.archivo_config, "r") as f:
                fecha_str = json.load(f).get("system", {}).get("last_report_date")
                if fecha_str:
                    return datetime.strptime(fecha_str, "%Y-%m-%d").date()
        except (json.JSONDecodeError, KeyError, FileNotFoundError, ValueError):
            pass

        # Si falla o no existe, reiniciamos el contador al último lunes
        hoy = date.today()
        ultimo_lunes = hoy - timedelta(days=hoy.weekday())
        self.update_last_report_date(ultimo_lunes)
        return ultimo_lunes

    def update_last_report_date(self, nueva_fecha: date):
        """Actualiza el marcador de tiempo tras descargar un reporte exitosamente."""
        if not os.path.exists(self.archivo_config):
            return
        try:
            with open(self.archivo_config, "r") as f:
                config = json.load(f)
            config.setdefault("system", {})["last_report_date"] = nueva_fecha.strftime("%Y-%m-%d")
            with open(self.archivo_config, "w") as f:
                json.dump(config, f, indent=4)
        except (json.JSONDecodeError, OSError) as e:
            print(f"[ConfigManager] Error al actualizar fecha de reporte: {e}")

    def save_last_dashboard(self, data: dict):
        """Guarda una caché local de las predicciones en caso de que se caiga el internet."""
        if not data: return
        try:
            with open(self.archivo_cache_dashboard, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"[ConfigManager] No se pudo guardar la cache: {e}")

    def get_last_dashboard(self) -> dict:
        """Rescata las predicciones de la caché local para que la UI no se rompa sin red."""
        if not os.path.exists(self.archivo_cache_dashboard):
            return {}
        try:
            with open(self.archivo_cache_dashboard, "r") as f:
                return json.load(f)
        except:
            return {}