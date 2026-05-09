import flet as ft

class HelpIcon(ft.Container):
    def __init__(self, help_id: int):
        super().__init__()

        # --- Definición de los Badges (Componentes visuales) ---
        def create_badge(text, bg, color):
            return ft.Container(
                content=ft.Text(text, size=10, weight="bold", color=color),
                bgcolor=bg,
                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                border_radius=10
            )

        superavit = create_badge("Superávit", "#E8FCE8", "#2E7D32")
        deficit = create_badge("Déficit", "#FCE8E8", "#D32F2F")
        stable = create_badge("Estable", "#F0EFE9", "#8D7A66")
        
        # Badge Dinámico Online/Offline
        is_online = help_id == 1
        btn_sync = ft.Container(
            content=ft.Text("● Online" if is_online else "● Offline", 
                           size=12, color="#2E7D32" if is_online else "#C85050", weight="bold"),
            bgcolor="#E8FCE8" if is_online else "#FCE8E8",
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=15
        )
        
        # --- Configuración del Contenido según ID ---
        # Ahora en lugar de solo texto, guardamos una LISTA de controles
        self.help_content = []

        if help_id == 1:
            self.help_content = [
                ft.Row([
                    ft.Text("Presiona el botón", weight="bold", color=ft.colors.ON_SURFACE), 
                    btn_sync, ft.Text("para buscar", weight="bold", color=ft.colors.ON_SURFACE)
                ], wrap=True, spacing=5),
                ft.Text("los productos y predicciones más recientes.", weight="bold", color=ft.colors.ON_SURFACE)
            ]
        elif help_id == 2:
            self.help_content = [
                ft.Row([ft.Text("Para poder presionar", weight="bold", color=ft.colors.ON_SURFACE), btn_sync], spacing=5),
                ft.Text("vuelva a tener conexión o reintente mas tarde.", weight="bold", color=ft.colors.ON_SURFACE)
            ]
        elif help_id == 3:
            self.help_content = [
                ft.Text("Significado de la etiqueta de prediccion", weight="bold", color=ft.colors.ON_SURFACE),
                ft.Row([superavit, ft.Text(": ", weight="bold", color=ft.colors.ON_SURFACE)], spacing=5),
                ft.Row([deficit, ft.Text(": ", weight="bold", color=ft.colors.ON_SURFACE)], spacing=5),
                ft.Row([stable, ft.Text(": ", weight="bold", color=ft.colors.ON_SURFACE)], spacing=5)
            ]
        else:
            self.help_content = [ft.Text(self.messages.get(help_id, "Información no disponible"))]

        # Icono principal
        self.content = ft.Icon(name=ft.icons.HELP_OUTLINE_ROUNDED, color="#8D7A66", size=20)
        self.padding = 5
        self.border_radius = 20
        self.mouse_cursor = ft.MouseCursor.CLICK
        self.on_hover = self._handle_hover
        self.on_click = self._show_help

    def _handle_hover(self, e):
        e.control.bgcolor = "#c9c9c9" if e.data == "true" else None
        e.control.update()

    def _show_help(self, e):
        dialog = ft.AlertDialog(
            title=ft.Text("Ayuda del Sistema", size=18, weight="bold"),
            # IMPORTANTE: Usamos Column para poder mostrar texto y contenedores juntos
            content=ft.Column(
                controls=self.help_content,
                tight=True, # Para que el diálogo no ocupe toda la pantalla
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            actions=[
                ft.TextButton("Entendido", on_click=lambda _: self.page.close(dialog))
            ],
            bgcolor=ft.colors.ON_SURFACE_VARIANT,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        self.page.open(dialog)