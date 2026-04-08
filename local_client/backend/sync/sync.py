import json
import os
import time
import threading
import requests
from datetime import datetime
from local_client.backend.db.sqlite_manager import SQLiteManager

class SyncDaemon:
    def __init__(self, db: SQLiteManager):
        self.db = db
        self.archivo_cola = "missing-items.txt"
        self.archivo_config = "settings.json"
        self.api_url = "http://127.0.0.1:8000/api/v1/ventas/sync"
        self.api_key = "tu_clave_secreta"

    def start(self):
        """Inicia el ciclo infinito en un hilo separado para no congelar la UI de Flet."""
        hilo = threading.Thread(target=self._ciclo_infinito, daemon=True)
        hilo.start()
        print("Daemon de sincronizacion iniciado en segundo plano")

    def _ciclo_infinito(self):
        time.sleep(5)
        while True:
            self.procesar_cola_pendientes()
            time.sleep(1800)

    def leer_config(self):
        if not os.path.exists(self.archivo_config):
            config_default
