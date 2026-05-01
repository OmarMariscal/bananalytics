import flet as ft
import datetime
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
        self.date = now.strftime("%A, %B %d, %Y")
        
        self.content = self._build_ui()

    def _build_ui(self):
        self.search_field = ft.TextField(
            expand=True,
            bgcolor=ft.colors.SURFACE_VARIANT,
            prefix_icon=ft.icons.SEARCH,
            hint_text="Search by product name or barcode...",
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
                ft.DataColumn(ft.Text("Product", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Barcode", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Classification", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Avg Sales", weight="bold", color="#8D7A66")),
                ft.DataColumn(ft.Text("Expected Sales", weight="bold", color="#8D7A66")),
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
                        ft.Text("Global Product Status", size=24, weight="bold", color=ft.colors.ON_SURFACE),
                        ft.Text(self.date, size=14, color="#8D7A66"),
                    ], spacing=0),
                    
                    ft.Row([
                        ft.Text("Comprehensive Product Predictions List", size=24, weight="bold", color=ft.colors.ON_SURFACE),
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
                                    ft.PopupMenuItem(text="Sort A-Z", on_click=lambda e: self._apply_sort_filter(sort="az")),
                                    ft.PopupMenuItem(text="Sort Z-A", on_click=lambda e: self._apply_sort_filter(sort="za")),
                                    ft.PopupMenuItem(), # Divisor
                                    ft.PopupMenuItem(text="Show Deficits Only", on_click=lambda e: self._apply_sort_filter(filter_type="deficit")),
                                    ft.PopupMenuItem(text="Show Surplus Only", on_click=lambda e: self._apply_sort_filter(filter_type="superavit")),
                                    ft.PopupMenuItem(),
                                    ft.PopupMenuItem(text="Clear All Filters", on_click=lambda e: self._apply_sort_filter(clear=True)),
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

        
        search_query = self.search_field.value.lower() if hasattr(self, 'search_field') else ""
        if search_query:
            alerts_to_display = [
                a for a in alerts_to_display 
                if search_query in a.product_name.lower() or search_query in str(a.barcode).lower()
            ]

        if self.current_filter:
            alerts_to_display = [a for a in alerts_to_display if a.type == self.current_filter]

        
        if self.current_sort == "az":
            alerts_to_display.sort(key=lambda a: a.product_name.lower())
        elif self.current_sort == "za":
            alerts_to_display.sort(key=lambda a: a.product_name.lower(), reverse=True)

        for alert in alerts_to_display:
            if alert.type == "deficit":
                bg_color, txt_color, label = "#FEE8E8", "#D00000", "DEFICIT"
            elif alert.type == "superavit":
                bg_color, txt_color, label = "#E8FCE8", "#2D6A4F", "SURPLUS"
            else:
                bg_color, txt_color, label = "#F5F5F5", "#757575", "NEUTRAL"

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
                                ft.Text(f"{alert.avg_weekly_sales} Units/Wk", color=ft.colors.ON_SURFACE)
                            ])
                        ),
                        
                        ft.DataCell(ft.Text(f"{alert.prediction} Units", weight="bold", color=ft.colors.ON_SURFACE)),
                    ]
                )
            )
        return rows

    def _open_details_dialog(self, alert_obj):
        dialog = ProductDetailDialog(alert_obj, self.main_page, self.backend)
        self.main_page.dialog = dialog
        dialog.open = True
        self.main_page.update()