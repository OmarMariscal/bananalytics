import flet as ft
import datetime
import unicodedata
from datetime import datetime
from frontend.components.product_details import ProductDetailDialog

class Products(ft.Container):
    def __init__(self, backend_service, page):
        super().__init__()
        self.expand = True 
        self.vertical_alignment = ft.MainAxisAlignment.START
        self.height = page.height
        
        self.backend = backend_service
        self.main_page = page
        self.list_alerts_original = self.backend.get_alerts() 
        
        self.current_filter = None 
        self.current_sort = None   

        now = datetime.now()
        now = datetime.now()
        # Diccionarios de traducción
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

        nombre_dia = dias_semana[now.weekday()]
        nombre_mes = meses[now.month - 1]
        dia_num = now.day
        anio = now.year

        self.date = f"{nombre_dia}, {nombre_mes} {dia_num}, {anio}"
                
        self.content = self._build_ui()

    def _normalize_text(self, text):
        if not text:
            return ""
        return ''.join(
            c for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        ).lower()

    def _build_ui(self):
        self.search_field = ft.TextField(
            expand=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            prefix_icon=ft.icons.SEARCH,
            hint_text="Busca por producto o por codigo de barras...",
            hint_style=ft.TextStyle(color=ft.colors.ON_SURFACE),
            border_radius=10,
            border_color=ft.colors.OUTLINE,
            text_size=14,
            color=ft.colors.ON_SURFACE,
            on_change=self._on_search_change
        )

        self.data_table = ft.DataTable(
            expand=True,
            column_spacing=40,
            show_checkbox_column=False,
            columns=[
                ft.DataColumn(ft.Text("Producto", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Código", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Clasificación", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Promedio de ventas", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Prédiccion de ventas", weight="bold", color="#8D7A66")),
            ],
            rows=self._get_product_rows()
        )

        ui = ft.Container(
            padding=30,
            expand=True,
            bgcolor=ft.colors.BACKGROUND,
            content=ft.Column(
                scroll=ft.ScrollMode.ADAPTIVE,
                expand=True,
                spacing=20,
                controls=[
                    ft.Column([
                        ft.Text("Estatus General de Productos", size=24, weight="bold", color=ft.colors.ON_SURFACE),
                        ft.Text(self.date, size=14, color="#8D7A66"),
                    ], spacing=0),
                    
                    ft.Row([
                        ft.Text("Lista Completa de Productos con Predicciones", size=24, weight="bold", color=ft.colors.ON_SURFACE),
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(ft.icons.WB_SUNNY_OUTLINED, size=16, color="#8D7A66"),
                                ft.Text("Weather-Adjusted", color="#8D7A66", size=12)
                            ], spacing=5),
                            bgcolor="#FDF3E7",
                            padding=ft.padding.symmetric(horizontal=12, vertical=6),
                            border_radius=10,
                            border=ft.border.all(1, "#E0E0E0")
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Row([
                        self.search_field,
                        ft.Container(
                            content=ft.PopupMenuButton(
                                icon=ft.icons.FILTER_ALT_OUTLINED,
                                icon_color="#8D7A66",
                                items=[
                                    ft.PopupMenuItem(text="Ordenar A-Z", on_click=lambda e: self._apply_sort_filter(sort="az")),
                                    ft.PopupMenuItem(text="Ordenar Z-A", on_click=lambda e: self._apply_sort_filter(sort="za")),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(text="Mostrar solo déficit", on_click=lambda e: self._apply_sort_filter(filter_type="deficit")),
                                    ft.PopupMenuItem(text="Mostrar solo superávit", on_click=lambda e: self._apply_sort_filter(filter_type="superavit")),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(text="Limpiar filtros", on_click=lambda e: self._apply_sort_filter(clear=True)),
                                ]
                            ),
                            border=ft.border.all(1, "#E0E0E0"),
                            border_radius=10
                        )
                    ]),

                    ft.Container(
                        bgcolor=ft.colors.SURFACE_VARIANT,
                        border_radius=15,
                        border=ft.border.all(1, ft.colors.OUTLINE),
                        width=float("inf"),
                        content=self.data_table 
                    )
                ]
            )
        )
        return ui

    def _on_search_change(self, e):
        self._apply_sort_filter()

    def _apply_sort_filter(self, sort=None, filter_type=None, clear=False):
        if clear:
            self.current_sort = None
            self.current_filter = None
            self.search_field.value = ""
        else:
            if sort: self.current_sort = sort
            if filter_type: self.current_filter = filter_type

        self.data_table.rows = self._get_product_rows()
        self.data_table.update()

    def _get_product_rows(self):
        rows = []
        alerts_to_display = self.list_alerts_original.copy()

        search_value = self.search_field.value if hasattr(self, 'search_field') else ""
        normalized_query = self._normalize_text(search_value)
        
        if normalized_query:
            alerts_to_display = [
                a for a in alerts_to_display 
                if normalized_query in self._normalize_text(a.product_name) or 
                   normalized_query in str(a.barcode).lower()
            ]

        if self.current_filter:
            alerts_to_display = [a for a in alerts_to_display if a.type == self.current_filter]

        if self.current_sort == "az":
            alerts_to_display.sort(key=lambda a: self._normalize_text(a.product_name))
        elif self.current_sort == "za":
            alerts_to_display.sort(key=lambda a: self._normalize_text(a.product_name), reverse=True)

        for alert in alerts_to_display:
            if alert.type == "deficit":
                bg_color, txt_color, label = "#FEE8E8", "#D00000", "DÉFICIT"
            elif alert.type == "superavit":
                bg_color, txt_color, label = "#E8FCE8", "#2D6A4F", "SUPERÁVIT"
            else:
                bg_color, txt_color, label = "#F5F5F5", "#757575", "ESTABLE"

            rows.append(
                ft.DataRow(
                    on_select_changed=lambda e, a=alert: self._open_details_dialog(a),
                    cells=[
                        ft.DataCell(
                            ft.Row([
                                ft.Image(src=alert.image_url, width=40, height=40, fit=ft.ImageFit.CONTAIN),
                                ft.Column([
                                    ft.Text(alert.product_name, weight="bold", color=ft.colors.ON_SURFACE),
                                    ft.Row([
                                        ft.Container(content=ft.Image(src="/icon_category.png", width=15, fit="contain")),
                                        ft.Text(alert.category, size=12, color="#8D7A66")
                                    ])
                                ], spacing=0)
                            ], spacing=10)
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.Container(content=ft.Image(src="/icon_barcode.png", width=15, fit="contain")),
                                ft.Text(alert.barcode, color="#8D7A66")
                            ])
                        ),
                        ft.DataCell(
                            ft.Container(
                                content=ft.Text(label, size=11, weight="bold", color=txt_color),
                                bgcolor=bg_color,
                                padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                border_radius=8
                            )
                        ),
                        ft.DataCell(
                            ft.Row([
                                ft.Container(content=ft.Image(src="/icon_arrow_b.png", width=15, fit="contain")),
                                ft.Text(f"{alert.avg_weekly_sales} Unidades/Semana", color=ft.colors.ON_SURFACE)
                            ])
                        ),
                        ft.DataCell(ft.Text(f"{alert.prediction} Unidades", weight="bold", color=ft.colors.ON_SURFACE)),
                    ]
                )
            )
        return rows

    def _open_details_dialog(self, alert_obj):
        dialog = ProductDetailDialog(alert_obj, self.main_page, self.backend)
        self.main_page.dialog = dialog
        dialog.open = True
        self.main_page.update()