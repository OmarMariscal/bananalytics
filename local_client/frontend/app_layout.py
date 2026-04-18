import flet as ft
from frontend.screens.dashboard import Dashboard
from frontend.screens.products import Products
from shared.models.info_config import ConfigStats
import time

class MainLayout(ft.Container):
    def __init__(self, page: ft.Page, backend_service):
        super().__init__()
        
        self.main_page = page
        self.backend_service = backend_service
        self.stats = self.backend_service.get_app_stats()
        self.expand = True
        self.bgcolor = "#F9F7F2"

        self.dynamic_content = ft.Container(
            expand=True,
            padding=30
        )

        new_dashboard = Dashboard()
        new_products = Products()

        self.txt_user_name = ft.Text(f"{self.stats.user_name}", weight="bold", size=20, color="#2D2114")
        self.txt_email = ft.Text(f"{self.stats.email}", size=12, color="#8D7A66")
        self.txt_theme_title = ft.Text("Cambiar tema", expand=True, weight="bold", size=14, color="#2D2114")
        self.txt_support_title = ft.Text("Contacto y soporte", size=14, weight="w500", color="#2D2114")

        self.user_popup = ft.Container(
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
                    ft.Text("support@bananalytics.com", size=12, color="#8D7A66")
                ]),
            ], tight=True, spacing=10),
            padding=20,
            width=300,
            bgcolor="#F9F7F2",
            border_radius=15,
            border=ft.border.all(1, "#E0E0E0"),
            shadow=ft.BoxShadow(blur_radius=15, color=ft.Colors.with_opacity(0.2, "black")),
            visible=False,
            left=60,
            top=150,
            on_hover=self._handle_popup_hover
        )
        
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
                            bgcolor="#C38441",
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
                        new_dashboard
                    ),

                    self._sidebar_button(
                        "/icon_products.png",
                        new_products
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

    def _update_content(self, new_view: ft.Control):
        self.dynamic_content.content = new_view
        self.dynamic_content.update()

    def _sidebar_button(self, icon_path, destination_view):
        return ft.Container(
            content=ft.Image(src=icon_path, width=60, fit="contain"),
            width=50,
            height=50,
            padding=10,
            border_radius=10,
            on_hover=lambda e: self._handle_hover(e),
            on_click=lambda _: self.update_content(destination_view),
        )

    def _handle_hover(self, e):
        e.control.bgcolor = "#3d2e1d" if e.data else "transparent"
        e.control.update()

    
    def _sidebar_button_user(self, icon_path):
        return ft.Container(
            content=ft.Image(src=icon_path, width=30, fit="contain"),
            width=50, height=50,
            padding=10, border_radius=10,
            on_hover=self._handle_user_hover,
        )

    def _handle_user_hover(self, e):

        e.control.bgcolor = "#3d2e1d" if e.data else "transparent"
        self.user_popup.visible = e.data
        
        e.control.update()
        self.update()

    def _handle_popup_hover(self, e):

        self.user_popup.visible = e.data
        e.control.update()
        self.update()

    def _update_content(self, new_view):
        self.dynamic_content.content = new_view
        self.dynamic_content.update()

    def _toggle_theme(self, e):
    
        if e.control.value:
            self.main_page.theme_mode = ft.ThemeMode.LIGHT
            bg_color = "#F9F7F2"
            text_color = "#2D2114"
        else:
            self.main_page.theme_mode = ft.ThemeMode.DARK
            bg_color = "#1E1E1E"
            text_color = "#F9F7F2"

        self.bgcolor = bg_color
        self.user_popup.bgcolor = bg_color

        self.txt_user_name.color = text_color
        self.txt_theme_title.color = text_color
        self.txt_support_title.color = text_color

        self.update()
        self.main_page.update()

    