import flet as ft
from shared.protocols.i_backend_service import BackendProtocol

class App:
    def __init__(self, svc: BackendProtocol, page: ft.Page):
        self.svc = svc
        self.page = page

        if self.svc.is_first_start():
            self._show_register()
        else:
            # Se cargan aquí UNA SOLA VEZ
            self.stats = self.svc.get_dashboard_stats()
            self.config = self.svc.get_app_stats()
            self.alerts = self.svc.get_alerts()
            self._show_dashboard()

    def _show_dashboard(self):
        # usa self.stats, self.config, self.alerts — sin volver a llamar al servicio
        ...

    def _show_register(self):
        ...

