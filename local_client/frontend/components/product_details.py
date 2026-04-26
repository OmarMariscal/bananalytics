import flet as ft
import datetime

class ProductDetailDialog(ft.AlertDialog):
    def __init__(self, alert, page, backend_service):
        super().__init__()
        self.alert = alert
        self.main_page = page
        self.backend_service = backend_service
        
        # Configuración del Diálogo
        self.modal = True
        self.shape = ft.RoundedRectangleBorder(radius=20)
        self.content_padding = 0
        
        # Formateo de fecha
        date_str = self.alert.objective_date.strftime("%b %d, %Y")

        self.content = ft.Container(
            width=1000,
            height=600,
            bgcolor="#F9F7F2",
            border_radius=25,
            content=ft.Column(
                [   ft.Container(
                        padding=ft.padding.only(left=25, right=15, top=15),
                        content=ft.Row(
                            [ft.Text("Detalles del producto", size=30, weight="bold", color="#8D7A66"),
                            ft.Container(
                                content=ft.Text("✕", size=25, weight="bold", color="#D32F2F"),
                                on_click=self.cerrar_dialogo,
                                padding=10,
                                border_radius=20,
                                on_hover=lambda e: setattr(e.control, "bgcolor", "#F0F0F0" if e.data == "true" else None) or e.control.update(),
                            )], 
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        )
                    ),

                    # --- CUERPO CON SCROLL ---
                    ft.Column(
                        [ft.Container(
                            border_radius=25,
                            bgcolor="white",
                            border=ft.border.all(1, "#F5E6D3"),
                            margin=20,
                            padding=20,
                            content=ft.Row(
                                [ft.Row(
                                    [ft.Container(
                                        content=ft.Image(src=self.alert.image_url, width=130, height=130, fit="contain"),
                                        bgcolor="#FDFBFA",
                                        border_radius=15,
                                        padding=10,
                                        border=ft.border.all(1, "#F0EFE9")
                                    ),
                                    # Detalles y Círculos
                                    ft.Column(
                                        [ft.Text(self.alert.product_name, size=28, weight="bold", color="#2D2114"),
                                        ft.Row(
                                            [ft.Container(content=ft.Image(src="/icon_category.png", width=20, fit="contain")),
                                            ft.Text(self.alert.category, size=14, color="#8D7A66")],
                                            alignment=ft.CrossAxisAlignment.CENTER
                                        ),
                                        ft.Container(
                                            content=ft.Row(
                                                [ft.Text("EAN:", size=12, weight="bold", color="#8D7A66"),
                                                ft.Text(f"{self.alert.barcode}", size=12, weight="bold", color="#2D2114")],
                                                alignment=ft.MainAxisAlignment.START
                                            ),
                                            bgcolor="#FDFBFA",
                                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                            border_radius=8,
                                            border=ft.border.all(0.5, "#8D7A66"),
                                            margin=ft.margin.only(top=10)
                                        )], 
                                        expand=1, spacing=5
                                    )],
                                    alignment=ft.MainAxisAlignment.CENTER
                                    ), 
                                    ft.Column(
                                        [self._build_status_indicators(self.alert.type),
                                        ft.Divider(height=20, color="transparent"),
                                        ft.Row(
                                            [self._stat_box("Avg Weekly Sales", f"{self.alert.avg_weekly_sales}", "Units", "#C38441"),
                                            self._stat_box("Expected Weekly Sales", f"{self.alert.prediction}", "Units", "#C38441"),], 
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN, # Centra las dos cajas
                                        spacing=0,
                                        width=450)],
                                        alignment=ft.MainAxisAlignment.SPACE_EVENLY, horizontal_alignment=ft.MainAxisAlignment.CENTER
                                )],
                                alignment=ft.MainAxisAlignment.SPACE_EVENLY
                            )
                        ),
                        ft.Container(
                            border_radius=25,
                            bgcolor="white",
                            border=ft.border.all(1, "#F5E6D3"),
                            margin=20,
                            padding=20,
                            content=(
                                ft.Text("Previous Sales History", size=20, weight="bold", color="#2D2114"),
                                # ESPACIO PARA LA GRÁFICA (Ahora con datos reales)
                                ft.Container(
                                    height=300, 
                                    bgcolor="#FDFBFA",
                                    padding=20, # Padding para que la gráfica no toque los bordes
                                    border_radius=20,
                                    border=ft.border.all(1, "#F0EFE9"),
                                    content=self._build_sales_chart() # <--- Llamada a la función
                                )
                            )
                        )], 
                        scroll=ft.ScrollMode.ADAPTIVE, expand=True, horizontal_alignment=ft.MainAxisAlignment.CENTER
                    )
                ], 
                spacing=0
            )
        )

    def cerrar_dialogo(self, e):
        self.open = False
        self.page.update()

    def _build_status_indicators(self, current_type):
        """Crea los tres círculos (Deficit, Surplus, Neutral)"""
        if current_type == "superavit":
            color="#2E7D32" 
        elif current_type == "deficit":
            color="#D32F2F"
        else:
            color="#6C757D"

        if current_type == "superavit":
            back_color="#E8FCE8" 
        elif current_type == "deficit":
            back_color="#FCE8E8"
        else:
            back_color="#E2E3E5"

        return ft.Column([
            ft.Row([
                self._status_circle("Deficit", "#F8D7DA", "#D32F2F", current_type == "deficit"),
                self._status_circle("Surplus", "#D4EDDA", "#2E7D32", current_type == "superavit"),
                self._status_circle("Neutral", "#E2E3E5", "#6C757D", current_type == "none"),
            ], spacing=10),
            ft.Row([
                ft.Text("Estatus:", size=15, weight="bold", color="#8D7A66"),
                ft.Container(
                content=ft.Text(current_type.upper(), size=12, weight="bold", color=color),
                bgcolor=back_color,
                padding=ft.padding.symmetric(horizontal=15, vertical=5),
                border_radius=8,
                )
            ])
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.CrossAxisAlignment.CENTER, spacing=15)

    def _status_circle(self, label, color, color_center, active):
        return ft.Column([
            ft.Container(
                width=45, height=45,
                bgcolor=color, #if active else "#F5F5F5",
                shape=ft.BoxShape.CIRCLE,
                border=ft.border.all(3, color if active else "transparent"),
                content=ft.Container(
                    bgcolor=color_center, #if active else "#F5F5F5",
                    shape=ft.BoxShape.CIRCLE,
                    margin=4 #if active else 0
                ) if active else None,
                shadow=ft.BoxShadow(blur_radius=10, color=color, spread_radius=1) #if active else None
            ),
            ft.Text(label, size=10, color="#8D7A66")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    def _stat_box(self, title, value, unit, color):
        return ft.Container(
            width=200,
            bgcolor="#FFF8F0",
            padding=20,
            border_radius=15,
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Image(src="/icon_arrow.png", width=20, fit="contain")),
                    ft.Text(title, size=13, color="#C38441", weight="w500"),
                ], spacing=8),
                ft.Column([
                    ft.Text(value, size=32, weight="bold", color="#2D2114"),
                    ft.Text(unit, size=14, color="#8D7A66"),
                ], alignment=ft.MainAxisAlignment.START, spacing=5)
            ], spacing=5),
            border=ft.border.all(1, "#F5E6D3")
        )

    def _build_sales_chart(self):
        history_data = self.backend_service.get_sales_history(self.alert.barcode)
        
        data_points = []
        for i, data in enumerate(history_data):
            # En versiones antiguas se llama directamente LineChartDataPoint
            data_points.append(
                ft.Linechartdatapoint(i, data["total_vendido"]) 
            )

        chart_line = ft.LineChartData(
            data_points=data_points,
            stroke_width=3,
            color="#C38441",
            curved=True,
            below_line_bgcolor=ft.colors.with_opacity(0.1, "#C38441"),
            below_line_gradient=ft.LinearGradient(
                begin=ft.alignment.top_center,
                end=ft.alignment.bottom_center,
                colors=[ft.colors.with_opacity(0.2, "#C38441"), ft.colors.TRANSPARENT],
            ),
        )

        # 4. Configurar Ejes (Labels)
        chart = ft.LineChart(
            data_series=[chart_line],
            border=ft.border.all(1, "#F0EFE9"),
            horizontal_grid_lines=ft.ChartGridLines(color="#F0EFE9", width=0.5, dash=[5, 5]),
            vertical_grid_lines=ft.ChartGridLines(color="#F0EFE9", width=0.5, dash=[5, 5]),
            left_axis=ft.ChartAxis(
                labels=[
                    ft.ChartAxisLabel(value=0, label=ft.Text("0", size=12, color="#8D7A66")),
                    ft.ChartAxisLabel(value=50, label=ft.Text("50", size=12, color="#8D7A66")),
                    ft.ChartAxisLabel(value=100, label=ft.Text("100", size=12, color="#8D7A66")),
                ],
                title=ft.Text("Sales Volume", color="#8D7A66", size=12, weight="bold"),
                title_size=40,
            ),
            bottom_axis=ft.ChartAxis(
                labels=[
                    # Mostramos la fecha formateada en el eje X
                    ft.ChartAxisLabel(
                        value=i, 
                        label=ft.Text(data["fecha"][5:], size=10, color="#8D7A66")
                    ) for i, data in enumerate(history_data)
                ],
            ),
            expand=True,
        )
        return chart