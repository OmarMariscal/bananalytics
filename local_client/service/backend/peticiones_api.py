"""
Cliente HTTP (Capa de Red).
Se encarga exclusivamente de negociar la conexión con el modelo en la Nube.
Maneja tokens JWT de seguridad y caídas por timeout.
"""

import os
import requests
import base64
# Ruta absoluta corregida para Pycharm
from shared.models.user import User


class ApiClient:
    def __init__(self):
        llave_encriptada = "QmFuQW5hbHl0aWNzLUFQSS1LRVktMjEtMTEtMDUtMTAtMjktMDEtUk9nM2xJMC00TWFSZzRkMA=="
        self.api_key = base64.b64decode(llave_encriptada).decode("utf-8")
        self.base_url = "https://bananalytics.onrender.com/api/v1"

    def check_health(self) -> bool:
        """Ping básico para validar que el servidor no está reiniciándose."""
        try:
            respuesta = requests.get(f"{self.base_url}/health", timeout=3)
            if respuesta.status_code == 200:
                datos = respuesta.json()
                return datos.get("status") == "online" and datos.get("base_datos") == "conectada"
            return False
        except requests.exceptions.RequestException:
            return False

    def register_user(self, user: User, ubicacion: dict) -> dict:
        """
        Intercambia las credenciales iniciales de la tienda por un JWT permanente.
        Utiliza una Master API Key por seguridad en este paso inicial.
        """
        url_registro = f"{self.base_url}/business/register"
        payload = {
            "name": user.name,
            "email": user.email,
            "city": ubicacion.get("ciudad", "Guadalajara"),
            "lat": ubicacion.get("latitud", 20.6596),
            "lng": ubicacion.get("longitud", -103.3496)
        }
        headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

        try:
            response = requests.post(url_registro, json=payload, headers=headers, timeout=10)
            data = response.json()

            if response.status_code == 201:
                return {
                    "status": "exito",
                    "id_negocio": data.get("id_negocio"),
                    "token": data.get("token")
                }
            elif response.status_code == 409:
                return {"status": "email_repeated", "mensaje": data.get("mensaje")}
            return {"status": "fail", "mensaje": "Error interno del servidor."}
        except requests.exceptions.RequestException:
            return {"status": "fail", "mensaje": "Error de red."}

    def get_dashboard_data(self, store_id: str, token: str) -> dict:
        """Descarga las predicciones de Machine Learning."""
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            respuesta = requests.get(f"{self.base_url}/business/{store_id}/predictions", headers=headers, timeout=10)
            return respuesta.json() if respuesta.status_code == 200 else {}
        except requests.exceptions.RequestException:
            return {}

    def get_product_data(self, store_id: str, barcode: str, token: str) -> dict:
        """Descarga el historial de ventas específico para dibujar la gráfica de detalle."""
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            respuesta = requests.get(f"{self.base_url}/business/{store_id}/{barcode}", headers=headers, timeout=10)
            return respuesta.json() if respuesta.status_code == 200 else {}
        except requests.exceptions.RequestException:
            return {}

    def get_weekly_report(self, store_id: str, token: str) -> dict:
        """Recibe el archivo binario Base64 del reporte PDF."""
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            respuesta = requests.get(f"{self.base_url}/business/{store_id}/report", headers=headers, timeout=20)
            return respuesta.json() if respuesta.status_code == 200 else {}
        except requests.exceptions.RequestException:
            return {}

    def sync_sales(self, paquete: dict, token: str) -> bool:
        """Sube el paquete masivo de ventas a la API."""
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        try:
            respuesta = requests.post(f"{self.base_url}/ventas/sync", json=paquete, headers=headers, timeout=15)
            return respuesta.status_code == 200
        except requests.exceptions.RequestException:
            return False