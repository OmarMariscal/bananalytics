import flet as ft

class HelpIcon(ft.Container):
    def __init__(self, help_id: int, aux, callback=None, data_package=None):
        super().__init__()
        
        self.callback = callback
        self.data_package = data_package
        
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
        
        is_online = help_id == 1
        btn_sync = ft.Container(
            content=ft.Text("● Online" if is_online else "● Offline", 
                           size=12, color="#2E7D32" if is_online else "#C85050", weight="bold"),
            bgcolor="#E8FCE8" if is_online else "#FCE8E8",
            padding=ft.padding.symmetric(horizontal=12, vertical=6),
            border_radius=15
        )

        self.help_id = help_id
        self.aux = aux
        self.title_dilog=""

        self.help_id = help_id
        self.aux = aux
        self.title_dilog=""
        self.help_content = []

        if help_id == 1:
            self.title_dilog="Estatus: Conectado (Online)"
            self.help_content = [
                ft.Row([
                    ft.Text("Presiona el botón", weight="bold", color=ft.colors.ON_SURFACE), 
                    btn_sync, ft.Text("para buscar", weight="bold", color=ft.colors.ON_SURFACE)
                ], wrap=True, spacing=5),
                ft.Text("los productos y predicciones más recientes.", weight="bold", color=ft.colors.ON_SURFACE)
            ]
        elif help_id == 2:
            self.title_dilog="Estatus: Sin Internet (Offline)"
            self.help_content = [
                ft.Row([ft.Text("Para poder presionar", weight="bold", color=ft.colors.ON_SURFACE), btn_sync], spacing=5),
                ft.Text("vuelva a tener conexión o reintente mas tarde.", weight="bold", color=ft.colors.ON_SURFACE)
            ]
        elif help_id == 3:
            self.title_dilog="Significado de la etiqueta de prediccion"
            self.help_content = [
                ft.Row([superavit, ft.Text(": ", weight="bold", color=ft.colors.ON_SURFACE), 
                        ft.Text("Se predice que habra un aumento de venta de este producto a comparacion de su venta medio", weight="bold", color=ft.colors.ON_SURFACE)], 
                        spacing=5),
                ft.Row([deficit, ft.Text(": ", weight="bold", color=ft.colors.ON_SURFACE),
                        ft.Text("Se predice que se vendera menos este producto a comparacion de su venta promedio", weight="bold", color=ft.colors.ON_SURFACE)], 
                        spacing=5),
                ft.Row([stable, ft.Text(": ", weight="bold", color=ft.colors.ON_SURFACE),
                        ft.Text("Este producto tendra una venta igual o similar a comparacion de su venta promedio", weight="bold", color=ft.colors.ON_SURFACE)], 
                        spacing=5),
            ]
        elif help_id == 4:
            self.title_dilog="¿Qué es el Margen de Error?"
            self.help_content = [
                ft.Text(f"El signo ± significa que la prediccion puede ser mayor en {aux} unidades arriba o abajo", weight="bold", color=ft.colors.ON_SURFACE),
                ft.Text("de lo que se dice en la prediccion", weight="bold", color=ft.colors.ON_SURFACE),
            ]

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
        self.dialog = ft.AlertDialog(
            title=ft.Text(self.title_dilog, size=18, weight="bold"),
            content=ft.Column(
                controls=self.help_content,
                tight=True,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            actions=[
                ft.TextButton("Entendido", on_click=self.close_help)
            ],
            bgcolor=ft.colors.ON_SURFACE_VARIANT,
            shape=ft.RoundedRectangleBorder(radius=12),
        )
        
        e.page.open(self.dialog)

    def close_help(self, e):
        e.page.close(self.dialog)
        
        if self.callback is not None and self.data_package is not None:
            self.callback(self.data_package)