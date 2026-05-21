import flet as ft
import unicodedata
from datetime import datetime
import traceback
from frontend.components.product_details import ProductDetailDialog
from frontend.components.marquesin_text import TextoMarquesina
from frontend.components.help import HelpIcon
from frontend.components.image_cache import ImageCacheManager
from frontend.components.loading_dialog import LoadingDialog
from frontend.components.show_error import ShowError

class Products(ft.Container):
    def __init__(self, page, alerts, backend_service):
        super().__init__()
        self.expand = True 
        self.page = page
        self.backend_service = backend_service
        self.list_alerts_original = alerts 
        
        self.current_filter = None 
        self.current_sort = None   

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
                ft.DataColumn(ft.Row([ft.Text("Clasificación", weight="bold", color="#8D7A66"), HelpIcon(help_id=3, aux="")])),
                ft.DataColumn(ft.Text("Promedio de ventas", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Prédiccion de ventas", weight="bold", color="#8D7A66")),
            ],
            rows=self._get_product_rows()
        )

        ui = ft.Container(
            padding=30,
            expand=True,
            alignment=ft.alignment.top_left,
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

        if len(alerts_to_display) == 0:
            path_local = ImageCacheManager.get_local_image_path("")
            self.product_name_display = TextoMarquesina(
                texto="Sin alertas pendientes", 
                ancho_max=340,
                size_text=14,
                color=ft.colors.ON_SURFACE
            )
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(
                            ft.Row([
                                ft.Image(src=path_local, width=40, height=40, fit=ft.ImageFit.CONTAIN),
                                self.product_name_display
                            ], spacing=10)
                        ),
                        ft.DataCell(ft.Row([ft.Text("", color="#8D7A66")])),
                        ft.DataCell(ft.Text("", color="#8D7A66")),
                        ft.DataCell(ft.Text("", color="#8D7A66")),
                        ft.DataCell(ft.Text("", color="#8D7A66")),
                    ]
                )
            )

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
            path_local = ImageCacheManager.get_local_image_path(alert.image_url)
            if alert.type == "deficit":
                bg_color, txt_color, label = "#FEE8E8", "#D00000", "DÉFICIT"
            elif alert.type == "superavit":
                bg_color, txt_color, label = "#E8FCE8", "#2D6A4F", "SUPERÁVIT"
            else:
                bg_color, txt_color, label = "#F5F5F5", "#757575", "ESTABLE"
            
            self.product_name_display = TextoMarquesina(
                texto=alert.product_name, 
                ancho_max=340,
                size_text=14,
                color=ft.colors.ON_SURFACE
            )

            rows.append(
                ft.DataRow(
                    on_select_changed=lambda e, a=alert: self._open_details_dialog(a),
                    cells=[
                        ft.DataCell(
                            ft.Row([
                                ft.Image(src=path_local, width=40, height=40, fit=ft.ImageFit.CONTAIN),
                                ft.Column([
                                    self.product_name_display,
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
        self.loading_dialog = LoadingDialog("Obteniendo información del producto...")
        self.page.open(self.loading_dialog)

        try:
            full_history = self.backend_service.get_sales_history(alert_obj.barcode)
            history_data = full_history[-90:] if full_history else []
            
            self.page.close(self.loading_dialog)
        except Exception as ex:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"Error: {__name__}\nDiagnóstico: {error}")
            self.page.close(self.loading_dialog)
            print("------------------------------------------------------------------")
            
            esperar_usuario = self._show_error_dialog(
                title="Error de historial de ventas", 
                menssage="Error al cargar el historial de ventas",
                usar_evento=True
            )
            
            if esperar_usuario:
                esperar_usuario.wait()

            history_data=[]

        data_package = {
            "alert": alert_obj,
            "history": history_data
        }
        
        def reopen_function(pkg):
            dialog = ProductDetailDialog(pkg, self.page, reopen_function)
            self.page.open(dialog)
        
        reopen_function(data_package)
    
    def _show_error_dialog(self, title, menssage, usar_evento=True): # 👈 Agregamos usar_evento por defecto
        dialog = ShowError(self.page, title, menssage, usar_evento=usar_evento)
        self.page.open(dialog)
        return dialog.click_event