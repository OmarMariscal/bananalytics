import flet as ft
import datetime
from datetime import datetime
from frontend.components.product_details import ProductDetailDialog

class Dashboard(ft.Container):
    def __init__(self, backend_service, page):  # ← Agregar page
        super().__init__()
        self.main_page = page
        self.backend_service = backend_service
        self.expand = True
        self.padding = 0

        # Obtenemos los datos del backend
        self.list_alerts = self.backend_service.get_alerts()
        now = datetime.now()
        self.date = now.strftime("%A, %B %d, %Y")
        self.server_status = self.backend_service.get_server_status()
        self.server_status_color = "#E8FCE8" if self.server_status else "#FCE8E8"
        self.server_status_text = "#2E7D32" if self.server_status else "#C85050"
        self.server_status = "● Online" if self.server_status else "● Offline"

        # Estructura principal: Fila con dos grandes columnas
        self.content = ft.Row(
            controls=[
                # --- SECCIÓN IZQUIERDA (Estadísticas y Gráficas) ---
                self._build_left_section(),

                # --- SECCIÓN DERECHA (Product Intelligence) ---
                self._build_right_section()
            ],
            expand=True,
            spacing=0 # Sin espacio para que el panel derecho se pegue al borde
        )

    def _build_left_section(self):
        """Construye la parte izquierda del dashboard (Estadísticas principales)"""
        return ft.Container(
            expand=3, # Ocupa 3 partes del ancho total
            padding=30,
            content=ft.Column(
                controls=[
                    # Encabezado
                    ft.Row([
                        ft.Column([
                            ft.Text("Global Product Status", size=24, weight="bold", color="#2D2114"),
                            ft.Text(self.date, size=14, color="#8D7A66"),
                        ], spacing=2),
                        ft.Container(
                            content=ft.Text(self.server_status, size=12, color=self.server_status_text, weight="bold"),
                            bgcolor=self.server_status_color,
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=15
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=20, color="transparent"),
                    
                    # Fila de tarjetas de estadísticas (Ejemplo visual)
                    ft.Row([
                        self._stat_card("Total Scans Today", "1,247", "/icon_scaner.png", "#FDF3E7", "#C38441"),
                        self._stat_card("Active Predictions", "23", "/icon_spyco.png", "#E8FCE8", "#2E7D32"),
                        self._stat_card("Pending Offline Syncs", "8", "/icon_sky.png", "#FDF3E7", "#C38441"),
                    ], spacing=20),
                    
                    # Aquí iría tu gráfica en el futuro
                    ft.Container(
                        expand=True,
                        bgcolor="white",
                        border_radius=15,
                        border=ft.border.all(1, "#E0E0E0"),
                        margin=ft.margin.only(top=20),
                        padding=20,
                        content=ft.Text("Sales Predictions vs Actuals (Gráfica aquí)", color="#8D7A66")
                    )
                ],
                expand=True
            )
        )

    def _build_right_section(self):
        """Construye el panel derecho dinámico de alertas de productos"""
        
        # Generamos la lista de tarjetas iterando sobre los datos del backend
        alert_cards = []
        for alert in self.list_alerts:
            alert_cards.append(self._create_alert_card(alert))

        return ft.Container(
            expand=1, # Ocupa 1 parte del ancho total
            bgcolor="#FDFBFA", # Un color ligeramente distinto para diferenciar el panel
            border=ft.border.only(left=ft.BorderSide(1, "#E0E0E0")),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Text("Product Intelligence", size=18, weight="bold", color="#2D2114"),
                    ft.Text("AI-powered demand predictions", size=12, color="#8D7A66"),
                    ft.Divider(height=20, color="transparent"),
                    
                    # ListView hace que la lista sea scrolleable si hay muchos productos
                    ft.ListView(
                        controls=alert_cards,
                        spacing=15,
                        expand=True
                    )
                ],
                expand=True
            )
        )

    def _create_alert_card(self, alert):
        # ... (Tu lógica de badge se mantiene igual) ...

        def on_hover(e):
            if e.data == "true":  # Mouse entra
                e.control.scale = 1.08
                e.control.bgcolor = "#FFFBF8"  # Color más cálido
            else:  # Mouse sale
                e.control.scale = 1.0
                e.control.bgcolor = "white"
            
            e.control.update()

        def open_details(e):
            # Importante: usamos self.page que Flet asigna automáticamente al control
            dialog = ProductDetailDialog(alert, self.page, self.backend_service)
            self.page.overlay.append(dialog)
            dialog.open = True
            self.main_page.update()

        # Lógica de colores del badge (resumida para el ejemplo)
        if alert.type == "deficit":
            badge_bg, badge_color, badge_text = "#FCE8E8", "#D32F2F", f"Deficit: {alert.prediction} units"
        elif alert.type == "superavit":
            badge_bg, badge_color, badge_text = "#E8FCE8", "#2E7D32", f"Surplus: {alert.prediction} units"
        else:
            badge_bg, badge_color, badge_text = "#F0EFE9", "#8D7A66", "Stable"

        return ft.Container(
            bgcolor="white",
            border_radius=15,
            padding=15,
            border=ft.border.all(1, "#E0E0E0"),
            
            # --- ANIMACIÓN ---
            # Usamos la sintaxis que admite tu versión
            animate_scale=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            
            # --- EVENTOS ---
            on_hover=on_hover,
            on_click=open_details,
            
            content=ft.Row(
                controls=[
                    ft.Container(
                        content=ft.Image(
                            src=alert.image_url, 
                            height=70, 
                            width=60, 
                            fit="contain",
                            border_radius=8
                        ),
                        width=70,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text(alert.product_name, weight="bold", size=14, color="#2D2114"),
                            ft.Row([
                                ft.Image("/icon_calendar.png", width=12),
                                ft.Text(alert.objective_date.strftime("%b %d, %Y"), size=11, color="#8D7A66")
                            ], spacing=5),
                            ft.Container(
                                content=ft.Text(badge_text, size=10, weight="bold", color=badge_color),
                                bgcolor=badge_bg,
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                border_radius=10
                            )
                        ],
                        spacing=3,
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                spacing=15
            )
        )

    def _stat_card(self, title, value, icon, icon_bg, icon_color):
        """Función auxiliar para crear las tarjetas pequeñas de estadísticas de la izquierda"""
        return ft.Container(
            expand=1,
            bgcolor="white",
            border_radius=15,
            padding=20,
            border=ft.border.all(1, "#E0E0E0"),
            content=ft.Row([
                ft.Column([
                    ft.Text(title, size=14, color="#8D7A66"),
                    ft.Text(value, size=24, weight="bold", color="#2D2114"),
                ], spacing=5, expand=True),
                ft.Container(
                    content=ft.Image(src=icon, width=60, fit="contain"),
                    bgcolor=icon_bg,
                    padding=10,
                    border_radius=10
                )
            ])
        )