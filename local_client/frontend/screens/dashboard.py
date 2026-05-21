import flet as ft
from datetime import datetime
import traceback

from frontend.components.product_details import ProductDetailDialog
from frontend.components.marquesin_text import TextoMarquesina
from frontend.components.loading_dialog import LoadingDialog
from frontend.components.help import HelpIcon
from frontend.components.image_cache import ImageCacheManager
from frontend.components.show_error import ShowError

class Dashboard(ft.Container):
    def __init__(self, page, recharge, stats, alerts, backend_service, status_fetched):
        super().__init__()
        self.page = page
        self.dashboard_stats = stats
        self.list_alerts = alerts
        self.backend_service = backend_service
        self.expand = True
        self.padding = 0
        self.recharge = recharge
        self.status_fetched = status_fetched
        self.is_online = False
        self.label = ""
        self.date = ""
        self.status_button = ft.Container(on_click=self._handle_sync)
        
        self.main_content = ft.Container(
            content=ft.ProgressRing(), 
            alignment=ft.alignment.center,
            expand=True
        )
        self.content = self.main_content

    def did_mount(self):
        self._initial_load()
        
    def _initial_load(self):
        try:
            self._fetch_data_from_server()
            self._build_ui_content()
        except Exception as e:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"Error: {__name__}Diagnóstico: {error}")
            print("------------------------------------------------------------------")
            esperar_usuario = self._show_error_dialog("Error de dashboard", "Error al construir el dashboard", usar_evento=True)
            esperar_usuario.wait()
            self.page.window_close()
        finally:
            self.page.update()
            self.update()

    def _update_status_ui(self):
        if not self.status_fetched:
            self.loading_dialog = LoadingDialog("Obteniendo estatus del servidor, por favor espera...")
            self.page.open(self.loading_dialog)

            try:
                self.is_online = self.backend_service.get_server_status()
            except Exception as ex:
                error = traceback.format_exc()
                print("------------------------------------------------------------------")
                print(f"Error: {__name__}Diagnóstico: {error}")
                print("------------------------------------------------------------------")
                self.page.close(self.loading_dialog)
                esperar_usuario = self._show_error_dialog(
                    "Error de conexión", 
                    "No se pudo verificar el estatus del servidor, operando en modo Offline.", 
                    usar_evento=True
                )
                esperar_usuario.wait()
                self.is_online = False

            self.status_fetched = True 
            self.page.close(self.loading_dialog)
        
        color_bg = "#E8FCE8" if self.is_online else "#FCE8E8"
        color_text = "#2E7D32" if self.is_online else "#C85050"
        self.label = "● Online" if self.is_online else "● Offline"

        self.status_button.content = ft.Text(self.label, size=12, color=color_text, weight="bold")
        self.status_button.bgcolor = color_bg
        self.status_button.padding = ft.padding.symmetric(horizontal=12, vertical=6)
        self.status_button.border_radius = 15
        self.status_button.on_hover = lambda e: self._on_button_hover(e, color_bg)

    def _fetch_data_from_server(self):
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        now = datetime.now()
        self.date = f"{dias_semana[now.weekday()]}, {meses[now.month - 1]} {now.day}, {now.year}"

    def _build_ui_content(self):
        self._update_status_ui()
        self.content = ft.Row(
            controls=[
                self._build_left_section(),
                self._build_right_section()
            ],
            expand=True,
            spacing=0
        )

    def _handle_sync(self, e):
        self.loading_dialog = LoadingDialog("Intentando sincronizar con el servidor, por favor espera...")
        self.page.open(self.loading_dialog)

        is_sync = False
        try:
            is_sync = self.backend_service.sync()
            if is_sync:
                self.page.close(self.loading_dialog)
                self.status_fetched = False
                self.recharge() 
                return
            else:
                self.page.close(self.loading_dialog)
                esperar_usuario = self._show_error_dialog("Error de conexión", "No se pudo establecer conexión con el servidor", usar_evento=True)
                esperar_usuario.wait()
        except Exception as ex:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"Error: {__name__}Diagnóstico: {error}")
            print("------------------------------------------------------------------")
            self.page.close(self.loading_dialog)
            esperar_usuario = self._show_error_dialog("Error al sincronizar", "Durante el proceso de sincronización hubo un error, intente de nuevo", usar_evento=True)
            esperar_usuario.wait()
        
        if not is_sync and self.page:
            self._build_ui_content()
            self.update()

    def _on_button_hover(self, e, original_bg):
        e.control.bgcolor = ft.colors.BLACK12 if e.data == "true" else original_bg
        if e.control.page:
            e.control.update()

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
                        ], spacing=0),
                        ft.Row([
                            self.status_button,
                            HelpIcon(help_id= 1 if self.label == "● Online" else 2 , aux ="")
                        ],)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    
                    ft.Divider(height=20, color="transparent"),

                    ft.Row([
                        self._stat_card("Escaneos Totales del Día", self.dashboard_stats["total_scans_today"], "/icon_scaner.png", "#FDF3E7"),
                        self._stat_card("Predicciones Activas", self.dashboard_stats["active_predictions"], "/icon_spyco.png", "#E8FCE8"),
                        self._stat_card("Sincronizaciones Offline Pendientes", self.dashboard_stats["pending_syncs"], "/icon_sky.png", "#FDF3E7"),
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

        if len(self.list_alerts) != 0:
            for alert in self.list_alerts:
                alert_cards.append(self._create_alert_card(alert))
            list_products = ft.ListView(
                controls=alert_cards,
                spacing=15,
                expand=True
            )
        else:
            alert_cards.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text("Sin alertas pendientes", color="#8D7A66", weight="bold")
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    bgcolor=ft.colors.SURFACE_VARIANT,
                    border_radius=15,
                    padding=15,
                    margin=ft.margin.only(left=15, right=15),
                    border=ft.border.all(1, "#E0E0E0"),
                )
            )
            list_products = ft.ListView(
                controls=alert_cards,
                spacing=15,
                expand=True
            )
            
        return ft.Container(
            expand=1,
            bgcolor=ft.colors.BACKGROUND,
            border=ft.border.only(left=ft.BorderSide(1, "#E0E0E0")),
            padding=20,
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Column([
                                ft.Text("Panel de productos", size=18, weight="bold", color=ft.colors.ON_SURFACE),
                                ft.Text("AI-powered demand predictions", size=12, color="#8D7A66"),
                            ], alignment=ft.MainAxisAlignment.START, spacing=2),
                            HelpIcon(help_id=3, aux="")
                        ], 
                        alignment=ft.MainAxisAlignment.SPACE_EVENLY
                    ),
                    
                    ft.Divider(height=20, color="transparent"),
                    ft.Container(
                        content=list_products,
                        expand=True
                    ),
                ],
                expand=True,
            )
        )

    def _create_alert_card(self, alert):

        def on_hover(e):
            if e.data == "true":
                e.control.scale = 1.08
                e.control.bgcolor = ft.colors.OUTLINE
            else:
                e.control.scale = 1.0
                e.control.bgcolor = ft.colors.SURFACE_VARIANT
            e.control.update()

        def open_details(e):
            self.loading_dialog = LoadingDialog("Obteniendo información del producto...")
            self.page.open(self.loading_dialog)

            try:
                full_history = self.backend_service.get_sales_history(alert.barcode)
                history_data = full_history[-90:] 
            except Exception as ex:
                error = traceback.format_exc()
                print("------------------------------------------------------------------")
                print(f"Error: {__name__}Diagnóstico: {error}")
                print("------------------------------------------------------------------")
                self.page.close(self.loading_dialog)
                esperar_usuario = self._show_error_dialog(title="Error de historial de ventas", menssage="Error al cargar el historial de ventas", usar_evento=True)
                esperar_usuario.wait()
                history_data = []
        
            self.page.close(self.loading_dialog)
            
            data_package = {
                "alert": alert,
                "history": history_data
            }

            def reopen_function(pkg):
                dialog = ProductDetailDialog(pkg, self.page, reopen_function)
                self.page.open(dialog)

            reopen_function(data_package)

        if alert.type == "deficit":
            badge_bg, badge_color, badge_text = "#FCE8E8", "#D32F2F", f"Déficit: {alert.prediction} units"
        elif alert.type == "superavit":
            badge_bg, badge_color, badge_text = "#E8FCE8", "#2E7D32", f"Superávit: {alert.prediction} units"
        else:
            badge_bg, badge_color, badge_text = "#F0EFE9", "#8D7A66", "Estable"

        product_name_display = TextoMarquesina(
            texto=alert.product_name, 
            ancho_max=140,
            size_text=14,
            color=ft.colors.ON_SURFACE
        )

        path_local = ImageCacheManager.get_local_image_path(alert.image_url)

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
                            src=path_local, 
                            height=70, 
                            width=60, 
                            fit="contain",
                            border_radius=8
                        ),
                        width=70,
                    ),
                    ft.Column(
                        controls=[
                            product_name_display,
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
            if p.percentage_average_deviation != 0:
                dev = round(p.percentage_average_deviation,2)
                deviation_data.append({
                    "name": p.product_name,
                    "dev": dev,
                    "abs_dev": abs(dev)
                })

        top_deviations = sorted(deviation_data, key=lambda x: x["abs_dev"], reverse=True)[:25]
        num_items = len(top_deviations)
        dynamic_width = 600 / num_items if num_items != 0 else 1
        max_abs_val = max([x["abs_dev"] for x in top_deviations]) if top_deviations else 100
        y_limit = int(max_abs_val * 1.2)
        dynamic_lines = (y_limit if y_limit > 0 else 1) / 15

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

        chart = ft.BarChart(
            bar_groups=bar_groups,
            border=ft.border.all(1, "#F0EFE9"),
            interactive=True,
            groups_space=None, 

            tooltip_bgcolor=ft.colors.with_opacity(0.95, "#F9F7F2"),
            horizontal_grid_lines=ft.ChartGridLines(
                color=ft.colors.with_opacity(0.2, "#8D7A66"), 
                width=0.5,
                interval=dynamic_lines,
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
                            content=ft.Text(item["name"][:12], size=10, color="#8D7A66"),
                            rotate=ft.Rotate(angle=-0.5), 
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
    
    def _show_error_dialog(self, title, menssage, usar_evento=False):
        dialog = ShowError(self.page, title, menssage, usar_evento=usar_evento)
        self.page.open(dialog)
        return dialog.click_event

    def refresh_stats(self, stats):
        self.dashboard_stats = stats
        self._build_ui_content()
