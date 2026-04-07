from shared.models.prediction import PredictionAlert
from shared.models.info_config import ConfigStats
from shared.models.user import User

class BackendService:
    def get_alerts(self) -> list[PredictionAlert]:
        return
    
    def get_product_detail(self, barcode: str) -> PredictionAlert:
        return
    
    def get_dashboard_stats(self) -> dict:
        return

    #La validación debe ser con un archivo creado con el método create_configurations    
    def is_first_start(self) -> bool:
        return

    def register_user(self, user: User) -> dict:
        return
    
    def create_configurations(self) -> bool:
        return

    def get_sales_history(self) -> list[dict]:
        return
    
    def get_app_stats(self) -> ConfigStats:
        return
    
    def get_server_status(self) -> bool:
        return
