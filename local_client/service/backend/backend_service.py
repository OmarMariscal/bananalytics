from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User

from local_client.backend.db.sqlite_manager import SQLiteManager
from local_client.backend.sync.sync import SyncDaemon
from local_client.backend.config.config_manager import ConfigManager
from local_client.service.backend.peticiones_api import ApiClient

class BackendService:
    def __init__(self):
        self.db = SQLiteManager()
        self.config = ConfigManager()
        self.api = ApiClient()
        self.daemon = SyncDaemon(self.db)

        if not self.config.is_first_start():
            self.daemon.start()

    def get_alerts(self) -> list[PredictionAlert]:
        return []
    
    def get_product_detail(self, barcode: str) -> PredictionAlert:
        return
    
    def get_dashboard_stats(self) -> dict:
        return

    #La validación debe ser con un archivo creado con el método create_configurations    
    def is_first_start(self) -> bool:
        return self.config.is_first_start()

    def register_user(self, user: User) -> dict:
        respuesta_api = self.api.register_user(user)

        if respuesta_api["status"] == "exito":
            self.config.create_configuration(user, respuesta_api["id_negocio"])
            self.daemon.start()

        return respuesta_api
    
    def create_configurations(self) -> bool:
        return True

    def get_sales_history(self) -> list[dict]:
        return []
    
    def get_app_stats(self) -> ConfigStats:
        return self.config.get_app_stats()
    
    def get_server_status(self) -> bool:
        return True
