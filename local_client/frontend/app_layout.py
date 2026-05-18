import flet as ft
from frontend.screens.dashboard import Dashboard
from frontend.screens.products import Products
from frontend.components.loading_dialog import LoadingDialog
from frontend.components.image_cache import ImageCacheManager

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

        self.dashboard_stats = ""
        self.list_alerts = []
        self.status_fetched = False

        self._get_stats()
        self.new_dashboard = Dashboard(self.page, self._sync, self.dashboard_stats, self.list_alerts, self.backend_service, self.status_fetched)
        self.new_products = Products(self.page, self.list_alerts, self.backend_service)

        self.dynamic_content.content = self.new_dashboard

        self.sidebar = ft.Container(
            width=70,
            bgcolor="#2D2114",
            padding=ft.padding.symmetric(vertical=20, horizontal=0),
            content=ft.Column(
                controls=[
                    ft.Row([
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
                        ),
                    ],
                        alignment=ft.MainAxisAlignment.CENTER,
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
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            )
        )

        self.content = ft.Stack([
            ft.Row([self.sidebar, self.dynamic_content], expand=True, spacing=0),
            self.user_popup
        ], expand=True)
    
    def _get_stats(self):
        self.loading_dialog.actualizar_mensaje("Cargando información de stats, por favor espera...")
        self.loading_dialog.open = True
        self.page.update()
        self.dashboard_stats = self.backend_service.get_dashboard_stats()
        
        self.loading_dialog.actualizar_mensaje("Cargando lista de productos, por favor espera...")
        self.page.update()
        self.list_alerts = self.backend_service.get_alerts()
        
        # NUEVO: Sincronización de imágenes al iniciar
        self.loading_dialog.actualizar_mensaje("Sincronizando galería de imágenes local...")
        self.page.update()
        ImageCacheManager.sync_all_images(self.list_alerts)
        
        self.loading_dialog.open = False
        self.page.update()

    def _user_popup(self):
        self.loading_dialog = LoadingDialog("Cargando información de usuario, por favor espera...")
        self.loading_dialog.open = True
        self.page.dialog = self.loading_dialog
        self.page.update()

        self.stats = self.backend_service.get_app_stats()

        self.loading_dialog.open = False
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
                        value=self.stats.theme_mode,
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
            self.dynamic_content.content = self.new_dashboard
        elif view_name == "products":
            self.dynamic_content.content = self.new_products
            
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
        try:
            self.loading_dialog = LoadingDialog("Cargando informacion de stats, por favor espera...")
            self.loading_dialog.open = True
            self.page.dialog = self.loading_dialog
            self.page.update()
            self.dashboard_stats = self.backend_service.get_dashboard_stats()
            self.loading_dialog.actualizar_mensaje("Cargando lista de productos, por favor espera...")
            self.page.update()
            self.list_alerts = self.backend_service.get_alerts()
            
            # NUEVO: Limpiar y descargar todo nuevamente en cada sincronización
            self.loading_dialog.actualizar_mensaje("Actualizando caché de imágenes, por favor espera...")
            self.page.update()
            ImageCacheManager.sync_all_images(self.list_alerts)
            self.data_loaded = False
            self.page.update()

            self.new_dashboard = Dashboard(self.page, self._sync, self.dashboard_stats, self.list_alerts, self.backend_service, self.status_fetched)
            self.new_products = Products(self.page, self.list_alerts, self.backend_service)

            self.dynamic_content.content = self.new_dashboard
        finally:
            self.loading_dialog.open = False
            self.page.update()

    