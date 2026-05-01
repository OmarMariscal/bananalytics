import flet as ft
import datetime

class ProductDetailDialog(ft.AlertDialog):
    def __init__(self, alert, page, backend_service):
        super().__init__()
        self.alert = alert
        self.main_page = page
        self.backend_service = backend_service
        
        self.modal = True
        self.shape = ft.RoundedRectangleBorder(radius=20)
        self.content_padding = 0
        
        date_str = self.alert.objective_date.strftime("%b %d, %Y")

        self.content = ft.Container(
            width=1000,
            height=600,
            bgcolor=ft.colors.BACKGROUND,
            border_radius=25,
            content=ft.Column([  
                ft.Container(
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

                ft.Column(
                    [ft.Container(
                        border_radius=25,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        border=ft.border.all(1, "#F5E6D3"),
                        margin=20,
                        padding=20,
                        content=ft.Row([
                            ft.Row([
                                ft.Container(
                                    content=ft.Image(src=self.alert.image_url, width=130, height=130, fit="contain"),
                                    bgcolor=ft.colors.OUTLINE,
                                    border_radius=15,
                                    padding=10,
                                    border=ft.border.all(1, "#F0EFE9")
                                ),
                                ft.Column(
                                    [ft.Text(self.alert.product_name, size=28, weight="bold", color=ft.colors.ON_SURFACE),
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
                                        bgcolor=ft.colors.OUTLINE,
                                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                        border_radius=8,
                                        border=ft.border.all(0.5, "#8D7A66"),
                                        margin=ft.margin.only(top=10)
                                    )], 
                                    expand=1, spacing=5
                                )],
                                alignment=ft.MainAxisAlignment.CENTER
                            ), 
                            ft.Column([
                                self._build_status_indicators(self.alert.type),
                                ft.Divider(height=20, color="transparent"),
                                ft.Row(
                                    [self._stat_box("Promedio de Ventas Semanales", f"{self.alert.avg_weekly_sales}", "", 260),
                                    self._stat_box("Predicciones de Ventas", f"{self.alert.prediction}", f"Para el: {self.alert.objective_date}", 210),], 
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                spacing=0,
                                width=500
                                )],
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            )],
                            alignment=ft.MainAxisAlignment.SPACE_EVENLY
                        )
                    ),
                    ft.Container(
                        border_radius=25,
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        border=ft.border.all(1, "#F5E6D3"),
                        margin=20,
                        padding=20,
                        content=ft.Column([
                            ft.Text("Gráfica Histórica de Ventas", size=20, weight="bold", color=ft.colors.ON_SURFACE),
                            self._build_sales_chart()
                        ])
                    )], 
                    scroll=ft.ScrollMode.ADAPTIVE, expand=True, horizontal_alignment=ft.MainAxisAlignment.CENTER
                )],
                spacing=0
            )
        )

    def cerrar_dialogo(self, e):
        self.open = False
        self.page.update()

    def _build_status_indicators(self, current_type):
        if current_type == "superavit":
            color="#2E7D32" 
            back_color="#E8FCE8"
            status="superávit"
        elif current_type == "deficit":
            color="#D32F2F"
            back_color="#FCE8E8"
            status="déficit"
        else:
            color="#6C757D"
            back_color="#E2E3E5"
            status="estable"

        return ft.Column([
            ft.Row([
                self._status_circle("Déficit", "#FA9EA6", "#D32F2F", current_type == "deficit"),
                self._status_circle("Superávit", "#8FFFA9", "#2E7D32", current_type == "superavit"),
                self._status_circle("Estable", "#A7AAAA", "#6C757D", current_type == "none"),
            ], 
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
            ),
            
            ft.Row([
                ft.Text("Estatus:", size=15, weight="bold", color="#8D7A66"),
                ft.Container(
                    content=ft.Text(status.upper(), size=12, weight="bold", color=color),
                    bgcolor=back_color,
                    padding=ft.padding.symmetric(horizontal=15, vertical=5),
                    border_radius=8,
                )
            ], 
            alignment=ft.MainAxisAlignment.CENTER
            )
        ], 
        spacing=15,
        width=450,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _status_circle(self, label, color, color_center, active):
        return ft.Column([
            ft.Container(
                width=60, height=60,
                bgcolor=color,
                shape=ft.BoxShape.CIRCLE,
                border=ft.border.all(3, color if active else "transparent"),
                content=ft.Container(
                    bgcolor=color_center,
                    shape=ft.BoxShape.CIRCLE,
                    margin=4 #if active else 0
                ) if active else None,
                shadow=ft.BoxShadow(blur_radius=10, color=color, spread_radius=1)
            ),
            ft.Text(label, size=15, color="#8D7A66")
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5)

    def _stat_box(self, title, value, text, wight):
        return ft.Container(
            width=wight,
            bgcolor=ft.colors.ON_SURFACE_VARIANT,
            padding=20,
            border_radius=15,
            content=ft.Column([
                ft.Row([
                    ft.Container(content=ft.Image(src="/icon_arrow.png", width=20, fit="contain")),
                    ft.Text(title, size=13, color="#C38441", weight="w500"),
                ], spacing=8),
                ft.Column([
                    ft.Text(value, size=32, weight="bold", color=ft.colors.ON_SURFACE),
                    ft.Text(text, size=14, color="#8D7A66"),
                ], alignment=ft.MainAxisAlignment.START, spacing=5)
            ], spacing=5),
            border=ft.border.all(1, "#F5E6D3")
        )

    def _build_sales_chart(self):
        history_data = self.backend_service.get_sales_history(self.alert.barcode)
        
        volumes = [data["volume"] for data in history_data]
        max_volume = max(volumes) if volumes else 100
        
        top_y = int(max_volume * 1.3)
        
        if top_y < 10: top_y = 10

        data_points = []
        for i, data in enumerate(history_data):
            data_points.append(
                ft.LineChartDataPoint(i, data["volume"]) 
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

        y_labels = []
        for y_val in range(0, top_y + 1, 10):
            y_labels.append(
                ft.ChartAxisLabel(
                    value=y_val, 
                    label=ft.Text(str(y_val), size=12, color="#8D7A66")
                )
            )

        chart = ft.LineChart(
            data_series=[chart_line],
            border=ft.border.all(1, "#F0EFE9"),
            horizontal_grid_lines=ft.ChartGridLines(color="#F0EFE9", width=0.5),
            vertical_grid_lines=ft.ChartGridLines(color="#F0EFE9", width=0.5),
            
            left_axis=ft.ChartAxis(
                labels=y_labels,
                labels_interval=10,
                title=ft.Text("Cantidad", color="#8D7A66", size=17, weight="bold"),
                title_size=45,
            ),
            
            bottom_axis=ft.ChartAxis(
                labels_size=40, 
                labels=[
                    ft.ChartAxisLabel(
                        value=i, 
                        label=ft.Container(
                            content=ft.Text(data["date"], size=10, color=ft.colors.ON_SURFACE),
                            rotate=ft.Rotate(angle=-1), 
                            padding=ft.padding.only(top=20)
                        )
                    ) for i, data in enumerate(history_data)
                ],
                labels_interval=1, 
            ),
            min_y=0,
            max_y=top_y,
            expand=True,
        )
        return chart