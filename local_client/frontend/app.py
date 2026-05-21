import flet as ft
import traceback
import threading
from shared.protocols.i_backend_service import BackendProtocol
from frontend.screens.register_screen import RegisterScreen
from frontend.app_layout import MainLayout
from frontend.components.show_error import ShowError

class App:
    def __init__(self, svc: BackendProtocol, page: ft.Page):
        self.svc = svc
        self.page = page
        page.window_maximized = True

        page.theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                background="#FF8400",
                surface="#FDF3E7",
                surface_variant="white",
                on_surface="#2D2114",
                on_surface_variant="#FDF3E7",
                outline="#FFFBF8",
            )
        )

        page.dark_theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                background="#FF8400",
                surface="black",
                surface_variant="#1E1E1E",
                on_surface="#F9F7F2",
                on_surface_variant="#333333",
                outline="#333333"
            )
        )

        self.page.update()
        self.iniciar_app()

    def iniciar_app(self):
        start = True
        try:
            start = self.svc.is_first_start()
        except Exception as ex:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"Error: {__name__}Diagnóstico: {error}")
            print("------------------------------------------------------------------")
            
            esperar_usuario = self._show_error_dialog(
                title="Error al iniciar", 
                menssage="No se pudo iniciar la aplicación, favor de intentar más tarde",
                usar_evento=True
            )
            
            esperar_usuario.wait()
            
            # Cierre limpio de la app
            self.page.window_close()
            return

        if start:
            self._show_register()
            return

        self._start_layout()

    def _start_layout(self):
        pantalla_carga = ft.Container(
            content=ft.Row(
                controls=[
                    ft.Text(
                        "Construyendo interfaz, por favor espera...", 
                        size=25, 
                        color=ft.colors.ON_SURFACE, 
                        weight="bold")
                ],
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20
            ),
            expand=True,
            alignment=ft.alignment.center,
            bgcolor=ft.colors.BACKGROUND
        )
        
        self.page.add(pantalla_carga)
        self.page.update()

        self.layout = MainLayout(self.page, backend_service=self.svc)
        self.page.clean()
        self.page.add(self.layout)
        self.page.update()

    def _show_register(self):
        self.page.clean()
        registro = RegisterScreen(
            backend_service=self.svc,
            on_success=self._start_layout
        )
        self.page.add(registro)
        self.page.update()

    def _show_error_dialog(self, title, menssage, usar_evento=True):
        dialog = ShowError(self.page, title, menssage, usar_evento=usar_evento)
        self.page.open(dialog)
        return dialog.click_event