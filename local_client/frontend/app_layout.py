import flet as ft
import traceback
from frontend.screens.dashboard import Dashboard
from frontend.screens.products import Products
from frontend.components.loading_dialog import LoadingDialog
from frontend.components.image_cache import ImageCacheManager
from frontend.components.reports_button import ReportsFolderButton
from frontend.components.show_error import ShowError

class MainLayout(ft.Container):
    def __init__(self, page: ft.Page, backend_service):
        super().__init__()
        
        self.page = page
        self.backend_service = backend_service
        self.expand = True
        self.bgcolor = "transparent"

        self.dynamic_content = ft.Container(
            expand=True,
            padding=0,
        )
        
        self.user_popup = self._user_popup()
        
        self.dashboard_stats = {
            "total_scans_today": 0,
            "active_predictions": 0,
            "pending_syncs": 0,
            "is_online": True,
        }
        self.list_alerts = []
        self.status_fetched = False
        
        self._get_stats()
        
        self.new_dashboard = Dashboard(self.page, self._sync, self.dashboard_stats, self.list_alerts, self.backend_service, self.status_fetched)
        self.new_products = Products(self.page, self.list_alerts, self.backend_service)

        self.dynamic_content.content = self.new_dashboard
        self.report = ReportsFolderButton(self.page)

        self.sidebar = ft.Container(
            width=70,
            bgcolor="#2D2114",
            padding=ft.padding.symmetric(vertical=20, horizontal=0),
            content=ft.Column(
                controls=[
                    ft.Column([
                        ft.Container(
                            content=ft.Image(
                                src="/logo_only.png",
                                width=30,
                                fit="contain"
                            ),
                            bgcolor="#61492D",
                            border=ft.border.all(1, "#A78E73"),
                            border_radius=8,
                            padding=ft.padding.all(8),
                            width=45,
                            height=45,
                            alignment=ft.alignment.center
                        ),
                        ft.Container(height=30),

                        self._sidebar_button(
                            "/icon_dashboard.png",
                            "dashboard"
                        ),

                        self._sidebar_button(
                            "/icon_products.png",
                            "products"
                        ),

                        self._sidebar_button_user("/icon_user.png")
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ft.Column(
                        [self.report],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    )
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN
            )
        )

        self.content = ft.Stack([
            ft.Row([self.sidebar, self.dynamic_content], expand=True, spacing=0),
            self.user_popup
        ], expand=True)
    
    def _get_stats(self):
        self.loading_dialog.actualizar_mensaje("Cargando información de stats, por favor espera...")
        self.page.open(self.loading_dialog)

        try:
            self.dashboard_stats = self.backend_service.get_dashboard_stats()
        except Exception as e:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"\nError: {__name__}\nDiagnóstico: {error}\n")
            print("------------------------------------------------------------------")
            self.page.close(self.loading_dialog)
            esperar_usuario = self._show_error_dialog("Error de Stats", "Ha ocurrido un error durante la carga de stats", usar_evento=True)
            esperar_usuario.wait()
            self.page.open(self.loading_dialog)

        self.loading_dialog.actualizar_mensaje("Cargando lista de productos, por favor espera...")
        self.page.update()

        try:
            self.list_alerts = self.backend_service.get_alerts()
        except Exception as e:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"\nError: {__name__}\nDiagnóstico: {error}\n")
            print("------------------------------------------------------------------")
            self.page.close(self.loading_dialog)
            esperar_usuario = self._show_error_dialog("Error de productos", "Ha ocurrido un error durante la carga de productos", usar_evento=True)
            esperar_usuario.wait()
            self.page.open(self.loading_dialog)
        
        self.loading_dialog.actualizar_mensaje("Sincronizando galería de imágenes local...")
        self.page.update()

        ImageCacheManager.sync_all_images(self.list_alerts)
        
        self.page.close(self.loading_dialog)

    def _user_popup(self):
        self.loading_dialog = LoadingDialog("Cargando información de usuario, por favor espera...")
        self.page.open(self.loading_dialog)

        try:
            self.stats = self.backend_service.get_app_stats()
        except Exception as e:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"\nError: {__name__}\nDiagnóstico: {error}\n")
            print("------------------------------------------------------------------")
            self.page.close(self.loading_dialog)
            esperar_usuario = self._show_error_dialog("Error de usuario", "Ha habido un error durante la carga de la información de usuario", usar_evento=True)
            esperar_usuario.wait()
            self.page.window_close()
            return

        self.page.close(self.loading_dialog)

        if self.page.theme_mode == ft.ThemeMode.SYSTEM or self.page.theme_mode is None:
            es_modo_claro = (self.page.platform_brightness == ft.Brightness.LIGHT)
        else:
            es_modo_claro = (self.page.theme_mode == ft.ThemeMode.LIGHT)
        self.page.theme_mode = ft.ThemeMode.LIGHT if es_modo_claro else ft.ThemeMode.DARK
        self.page.update()

        self.txt_user_name = ft.Text(f"{self.stats.user_name}", weight="bold", size=20, color=ft.colors.ON_SURFACE)
        self.txt_email = ft.Text(f"{self.stats.email}", size=12, color="#8D7A66")
        self.txt_theme_title = ft.Text("Cambiar tema", expand=True, weight="bold", size=14, color=ft.colors.ON_SURFACE)
        self.txt_support_title = ft.Text("Contacto y soporte", size=14, weight="w500", color=ft.colors.ON_SURFACE)

        return ft.Container(
            content=ft.Column([
                self.txt_user_name,
                self.txt_email,
                ft.Divider(color="#F0EFE9"),
                ft.Row([
                    self.txt_theme_title,
                    ft.Container(content=ft.Image(src="/icon_moon.png",width=30,fit="contain")),
                    ft.Switch(
                        active_color="#C38441", 
                        value=es_modo_claro, 
                        on_change=self._toggle_theme
                    ),
                    ft.Container(content=ft.Image(src="/icon_sun.png",width=30,fit="contain")),
                ]),
                ft.Divider(color="#F0EFE9"),
                self.txt_support_title,
                ft.Row([
                    ft.Container(content=ft.Image(src="/icon_email.png",width=20,fit="contain")),
                    ft.Text("MonkeyCodeInc+BananalyticsSupport@gmail.com", size=12, color="#8D7A66")
                ]),
            ], tight=True, spacing=10),
            padding=20,
            width=350,
            bgcolor=ft.colors.BACKGROUND,
            border_radius=15,
            border=ft.border.all(1, "#E0E0E0"),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.colors.with_opacity(0.2, "black")),
            visible=False,
            left=60,
            top=150,
            on_hover=self._handle_popup_hover
        )

    def _update_content(self, view_name: str):
        if view_name == "dashboard":
            self.loading_dialog.actualizar_mensaje("Intentando sincronizar stats de dashboard, por favor espera...")
            self.page.open(self.loading_dialog)

            fresh_stats = {
                "total_scans_today": 0,
                "active_predictions": 0,
                "pending_syncs": 0,
                "is_online": True,
            }

            try:
                fresh_stats = self.backend_service.get_dashboard_stats()
            except Exception as e:
                error = traceback.format_exc()
                print("------------------------------------------------------------------")
                print(f"\nError: {__name__}\nDiagnóstico: {error}\n")
                print("------------------------------------------------------------------")
                self.page.close(self.loading_dialog)
                esperar_usuario = self._show_error_dialog("Error de Stats", "Ha habido un error durante la carga de stats", usar_evento=True)
                esperar_usuario.wait()

            self.page.close(self.loading_dialog)
            
            self.dynamic_content.content = self.new_dashboard
            
            self.dynamic_content.update()
            
            self.new_dashboard.refresh_stats(fresh_stats)
            
        elif view_name == "products":
            self.dynamic_content.content = self.new_products
            # También lo movemos aquí adentro para mantener la consistencia
            self.dynamic_content.update()

    def _sidebar_button(self, icon_path, view_name: str):
        return ft.Container(
            content=ft.Image(src=icon_path, width=60, fit="contain"),
            width=50,
            height=50,
            padding=10,
            border_radius=10,
            on_hover=lambda e: self._handle_hover(e),
            on_click=lambda _: self._update_content(view_name),
        )

    def _handle_hover(self, e):
        e.control.bgcolor = "#3d2e1d" if e.data == "true" else "transparent"
        e.control.update()

    def _sidebar_button_user(self, icon_path):
        return ft.Container(
            content=ft.Image(src=icon_path, width=30, fit="contain"),
            width=50, height=50,
            padding=10, border_radius=10,
            on_hover=self._handle_user_hover,
        )

    def _handle_user_hover(self, e):
        is_hovered = e.data == "true"
        e.control.bgcolor = "#3d2e1d" if is_hovered else "transparent"
        self.user_popup.visible = is_hovered
        
        e.control.update()
        self.update()

    def _handle_popup_hover(self, e):
        self.user_popup.visible = e.data
        e.control.update()
        self.update()

    def _toggle_theme(self, e):
        if e.control.value:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
            
        self.page.update()
    
    def _sync(self):
        self.loading_dialog.actualizar_mensaje("Cargando informacion de stats, por favor espera...")
        self.page.open(self.loading_dialog)

        try:
            self.dashboard_stats = self.backend_service.get_dashboard_stats()
        except Exception as e:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"\nError: {__name__}\nDiagnóstico: {error}\n")
            print("------------------------------------------------------------------")
            self.page.close(self.loading_dialog)
            esperar_usuario = self._show_error_dialog("Error de Stats", "Ha ocurrido un error durante la carga de stats", usar_evento=True)
            esperar_usuario.wait()
            self.page.open(self.loading_dialog)

        self.loading_dialog.actualizar_mensaje("Cargando lista de productos, por favor espera...")
        self.page.update()

        try:
            self.list_alerts = self.backend_service.get_alerts()
        except Exception as e:
            error = traceback.format_exc()
            print("------------------------------------------------------------------")
            print(f"\nError: {__name__}\nDiagnóstico: {error}\n")
            print("------------------------------------------------------------------")
            self.page.close(self.loading_dialog)
            esperar_usuario = self._show_error_dialog("Error de productos", "Ha ocurrido un error durante la carga de productos", usar_evento=True)
            esperar_usuario.wait()
            self.page.open(self.loading_dialog)
        
        self.loading_dialog.actualizar_mensaje("Actualizando caché de imágenes, por favor espera...")
        self.page.update()
        ImageCacheManager.sync_all_images(self.list_alerts)
        self.data_loaded = False
        self.page.update()

        self.new_dashboard = Dashboard(self.page, self._sync, self.dashboard_stats, self.list_alerts, self.backend_service, self.status_fetched)
        self.new_products = Products(self.page, self.list_alerts, self.backend_service)

        self.dynamic_content.content = self.new_dashboard
        self.page.close(self.loading_dialog)
        self.page.update()

    def _show_error_dialog(self, title, menssage, usar_evento=True):
        dialog = ShowError(self.page, title, menssage, usar_evento=usar_evento)
        self.page.open(dialog)
        return dialog.click_event