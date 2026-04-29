import flet as ft
from shared.protocols.i_backend_service import BackendProtocol
from frontend.screens.register_screen import RegisterScreen
from frontend.app_layout import MainLayout

class App:
    def __init__(self, svc: BackendProtocol, page: ft.Page):
        self.svc = svc

        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                background="#FF8400",
                surface="#FDF3E7",
                surface_variant = "white",
                on_surface="#2D2114",
                on_surface_variant="#FDF3E7",
                outline="#FFFBF8",
            )
        )

        page.dark_theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                background="#FF8400",
                surface="black",
                surface_variant = "#1E1E1E",
                on_surface="#F9F7F2",
                on_surface_variant="#333333",
                outline="#333333"
            )
        )
        
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