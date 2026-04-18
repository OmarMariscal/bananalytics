import flet as ft
from shared.protocols.i_backend_service import BackendProtocol
from frontend.screens.register_screen import RegisterScreen
from frontend.app_layout import MainLayout

class App:
    def __init__(self, svc: BackendProtocol, page: ft.Page):
        self.svc = svc
        self.page = page

        if self.svc.is_first_start():
            self._show_register()
            return

        self._iniciar_dashboard_completo()

    def _iniciar_dashboard_completo(self):
        self.page.clean()
        self.page.dialog = None
        self.page.update()

        self.stats = self.svc.get_dashboard_stats()
        self.config = self.svc.get_app_stats()
        self.alerts = self.svc.get_alerts()
        self.layout = MainLayout(self.page, backend_service=self.svc)
        self._show_dashboard()

    def _show_register(self):
        self.page.clean()
        registro = RegisterScreen(
            backend_service=self.svc,
            on_success=self._iniciar_dashboard_completo
        )
        self.page.add(registro)
        self.page.update()

    def _show_dashboard(self):
        self.page.clean()
        self.page.add(self.layout) 
        self.page.update()