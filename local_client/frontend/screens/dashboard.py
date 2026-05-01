import flet as ft
import datetime
from datetime import datetime
from frontend.components.product_details import ProductDetailDialog

class Dashboard(ft.Container):
    def __init__(self, backend_service, page):
        super().__init__()
        self.main_page = page
        self.backend_service = backend_service
        self.expand = True
        self.padding = 0

        self.list_alerts = self.backend_service.get_alerts()
        now = datetime.now()
        now = datetime.now()

        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        nombre_dia = dias_semana[now.weekday()]
        nombre_mes = meses[now.month - 1]
        dia_num = now.day
        anio = now.year

        self.date = f"{nombre_dia}, {nombre_mes} {dia_num}, {anio}"
                
        self.status_button = ft.Container(on_click=self._handle_sync)
        self._update_status_ui()

        self.content = ft.Row(
            controls=[
                self._build_left_section(),
                self._build_right_section()
            ],
            expand=True,
            spacing=0
        )

    def _update_status_ui(self):
        """Actualiza los colores y texto del botón de estatus basado en el backend"""
        is_online = self.backend_service.get_server_status()
        
        color_bg = "#E8FCE8" if is_online else "#FCE8E8"
        color_text = "#2E7D32" if is_online else "#C85050"
        label = "● Online" if is_online else "● Offline"

        self.status_button.content = ft.Text(label, size=12, color=color_text, weight="bold")
        self.status_button.bgcolor = color_bg
        self.status_button.padding = ft.padding.symmetric(horizontal=12, vertical=6)
        self.status_button.border_radius = 15
        
        self.status_button.on_hover = lambda e: self._on_button_hover(e, color_bg)

    def _on_button_hover(self, e, original_bg):
        e.control.bgcolor = ft.colors.BLACK12 if e.data == "true" else original_bg
        
        if e.control.page:
            e.control.update()

    def _handle_sync(self, e):
        """Función que se ejecuta al presionar el botón Online/Offline"""
        is_sync = self.backend_service.sync()

        if is_sync:
            self.list_alerts = self.backend_service.get_alerts()
            self._update_status_ui()
            
            self.content.controls = [
                self._build_left_section(),
                self._build_right_section()
            ]
            self.update()
        else:
            def close_dlg(e):
                confirm_dialog.open = False
                self.main_page.update()

            confirm_dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Error de Conexión"),
                content=ft.Text(
                    "No se pudo establecer comunicación con el servidor.\n"
                    "Por favor, verifica tu conexión a internet o intenta más tarde."
                ),
                actions=[
                    ft.TextButton("Entendido", on_click=close_dlg),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )

            self.main_page.dialog = confirm_dialog
            confirm_dialog.open = True
            self.main_page.update()

    def _build_left_section(self):
        return ft.Container(
            expand=3,
            padding=30,
            bgcolor=ft.colors.BACKGROUND,
            content=ft.Column(
                controls=[
                    ft.Row([
                        ft.Column([
                            ft.Text("Estatus General de Productos", size=24, weight="bold", color=ft.colors.ON_SURFACE),
                            ft.Text(self.date, size=14, color="#8D7A66"),
                        ], spacing=2),
                        
                        self.status_button
                        
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=20, color="transparent"),

                    ft.Row([
                        self._stat_card("Escaneos Totales del Día", "1,247", "/icon_scaner.png", "#FDF3E7"),
                        self._stat_card("Predicciones Activas", "23", "/icon_spyco.png", "#E8FCE8"),
                        self._stat_card("Sincronizaciones Offline Pendientes", "8", "/icon_sky.png", "#FDF3E7"),
                    ], spacing=20),
                    
                    ft.Container(
                        expand=True,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        border_radius=15,
                        border=ft.border.all(1, "#E0E0E0"),
                        margin=ft.margin.only(top=20),
                        padding=20,
                        content=ft.Column([
                            ft.Text("Principales Productos Destacados", color="#8D7A66"),
                            self._build_deviation_chart()
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    )
                ],
                expand=True
            )
        )

    def _build_right_section(self):

        alert_cards = []
        for alert in self.list_alerts:
            alert_cards.append(self._create_alert_card(alert))

        return ft.Container(
            expand=1,
            bgcolor=ft.colors.BACKGROUND,
            border=ft.border.only(left=ft.BorderSide(1, "#E0E0E0")),
            padding=10,
            content=ft.Column(
                controls=[
                    ft.Text("Panel de productos", size=18, weight="bold", color=ft.colors.ON_SURFACE),
                    ft.Text("AI-powered demand predictions", size=12, color="#8D7A66"),
                    ft.Divider(height=20, color="transparent"),
                    
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

        def on_hover(e):
            if e.data == "true":
                e.control.scale = 1.08
                e.control.bgcolor = ft.colors.OUTLINE
            else:  # Mouse sale
                e.control.scale = 1.0
                e.control.bgcolor = ft.colors.SURFACE_VARIANT
            
            e.control.update()

        def open_details(e):
            
            dialog = ProductDetailDialog(alert, self.page, self.backend_service)
            self.page.overlay.append(dialog)
            dialog.open = True
            self.main_page.update()

        if alert.type == "deficit":
            badge_bg, badge_color, badge_text = "#FCE8E8", "#D32F2F", f"Déficit: {alert.prediction} units"
        elif alert.type == "superavit":
            badge_bg, badge_color, badge_text = "#E8FCE8", "#2E7D32", f"Superávit: {alert.prediction} units"
        else:
            badge_bg, badge_color, badge_text = "#F0EFE9", "#8D7A66", "Estable"

        return ft.Container(
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=15,
            padding=15,
            margin=ft.margin.only(left=15, right=15),
            border=ft.border.all(1, "#E0E0E0"),
            
            animate_scale=ft.Animation(300, ft.AnimationCurve.DECELERATE),
            
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
                            ft.Text(alert.product_name, weight="bold", size=14, color=ft.colors.ON_SURFACE),
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

    def _stat_card(self, title, value, icon, icon_bg):
        """Función auxiliar para crear las tarjetas pequeñas de estadísticas de la izquierda"""
        return ft.Container(
            expand=1,
            bgcolor=ft.colors.SURFACE_VARIANT,
            border_radius=15,
            padding=20,
            border=ft.border.all(1, "#E0E0E0"),
            content=ft.Row([
                ft.Column([
                    ft.Text(title, size=14, color="#8D7A66"),
                    ft.Text(value, size=24, weight="bold", color=ft.colors.ON_SURFACE),
                ], spacing=5, expand=True),
                ft.Container(
                    content=ft.Image(src=icon, width=60, fit="contain"),
                    bgcolor=icon_bg,
                    padding=10,
                    border_radius=10
                )
            ])
        )
    
    def _build_deviation_chart(self):
        deviation_data = []
        for p in self.list_alerts:
            if p.avg_weekly_sales > 0:
                dev = round(((p.prediction - p.avg_weekly_sales) / p.avg_weekly_sales) * 100, 2)
                deviation_data.append({
                    "name": p.product_name,
                    "dev": dev,
                    "abs_dev": abs(dev)
                })

        top_deviations = sorted(deviation_data, key=lambda x: x["abs_dev"], reverse=True)[:25]
        num_items = len(top_deviations)
        dynamic_width = 40 if num_items < 5 else 25 if num_items < 15 else 15

        bar_groups = []
        for i, item in enumerate(top_deviations):
            bar_color = "#2E7D32" if item["dev"] >= 0 else "#D32F2F"
            
            bar_groups.append(
                ft.BarChartGroup(
                    x=i,
                    bar_rods=[
                        ft.BarChartRod(
                            from_y=0,
                            to_y=item["dev"],
                            width=dynamic_width,
                            color=bar_color,
                            border_radius=5,
                        )
                    ],
                )
            )

        max_abs_val = max([x["abs_dev"] for x in top_deviations]) if top_deviations else 100
        y_limit = int(max_abs_val * 1.2)

        chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(1, "#F0EFE9"),
            interactive=True,
            groups_space=None, 

            tooltip_bgcolor=ft.colors.with_opacity(0.95, "#F9F7F2"),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.with_opacity(0.2, "#8D7A66"), 
                width=0.5,
                interval=10,
            ),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=-y_limit, label=ft.Text(f"-{y_limit}%", size=10, color="#8D7A66")),
                    ft.ChartAxisLabel(value=0, label=ft.Text("0%", size=10, weight="bold", color="#8D7A66")),
                    ft.ChartAxisLabel(value=y_limit, label=ft.Text(f"{y_limit}%", size=10, color="#8D7A66")),
                ],
                labels_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(
                        value=i, 
                        label=ft.Container(
                            content=ft.Text(item["name"][:10], size=10, color="#8D7A66"),
                            rotate=ft.Rotate(angle=-1.1), 
                            padding=ft.padding.only(top=10)
                        )
                    ) for i, item in enumerate(top_deviations)
                ],
                labels_size=60,
            ),
            max_y=y_limit,
            min_y=-y_limit,
            expand=True,
        )
        return chart