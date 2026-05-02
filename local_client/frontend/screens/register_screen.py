import flet as ft
import re
from frontend.components.btn_validate import PrimaryButton
from shared.models.user import User

class RegisterScreen(ft.Column):
    def __init__(self, backend_service, on_success):
        super().__init__()

        self.backend_service = backend_service
        self.on_success = on_success
        
        self.bgcolor = "#F9F7F2"
        self.expand = True
        self.alignment = ft.MainAxisAlignment.CENTER

        self.logo_bananalytics = ft.Image(
            src="/logo_only.png",
            width=80,
            height=80,
            fit="contain"
        )

        self.icon_local = ft.Image(
            src="/icon_local.png",
            width=20,
            height=20,
            fit="contain"
        )

        self.name = ft.TextField(
            label="Nombre completo",
            hint_text="e.g., Margarita López",
            border_color="#E0D7C6",
            bgcolor="#FDFBF9",
            on_change=self._text_validate,
            text_size=14,
            height=50,
        )

        self.email = ft.TextField(
            label="Correo electronico",
            hint_text="e.g., support@bananalytics.com",
            border_color="#E0D7C6",
            bgcolor="#FDFBF9",
            on_change=self._email_validate,
            text_size=14,
            height=50,
        )

        self.error_name = ft.Text("", color="red", size=11, visible=False)
        self.error_email = ft.Text("", color="red", size=11, visible=False)

        self.btn_registro =  PrimaryButton(
            texto_usuario = "Finalizar Registro",
            accion_click = self._validar_y_enviar
        )

        self.location_note = ft.Container(
            bgcolor="#FDF7F0",
            border=ft.border.all(1, "#F3E6D5"),
            border_radius=8,
            padding=10,
            width=340,
            content=ft.Row(
                controls=[
                    self.icon_local,
                    ft.Text(
                        "Nota: La localización del negocio será\n"
                        "determinada automáticamente vía internet.",
                        size=13,
                        color="#8D7A66"
                    )
                ],
                alignment=ft.MainAxisAlignment.START,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True
            )
        )

        self.success_dialog = ft.AlertDialog(
            title=ft.Text("¡Registro Exitoso!"),
            content=ft.Text(""),
            bgcolor="#C0843F",
            actions=[ft.TextButton("Continuar", on_click=self._close_dialog)],
        )
        
        self.error_dialog = ft.AlertDialog(
            title=ft.Text("Ha ocurrido algo..."),
            content=ft.Text(""),
            bgcolor="#C0843F",
            actions=[ft.TextButton("Continuar", on_click=self._close_dialog)],
        )

        white_card = ft.Container(
            width=400,
            bgcolor="white",
            border_radius=12,
            padding=30,
            shadow=ft.BoxShadow(
                blur_radius=15,
                color=ft.colors.with_opacity(0.1, "black"),
            ),
            content=ft.Column(
                controls=[
                    self.logo_bananalytics,
                    ft.Text("BanAnalytics", size=22, weight="bold", color="#2D2114"),
                    ft.Text("Bienvenid@ a BanAnalytics", size=16, color="#4A3F35"),
                    ft.Text("Registrate para continuar", size=13, color="#8D7A66"),
                    ft.Divider(height=10, color="transparent"),
                    self.name,
                    self.error_name,
                    self.email,
                    self.error_email,
                    self.location_note,
                    ft.Divider(height=10, color="transparent"),
                    self.btn_registro,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            )
        )
        self.content = white_card

        self.controls = [
            ft.Row(
                controls=[white_card],
                alignment=ft.MainAxisAlignment.CENTER
            ),
            self.success_dialog,
            self.error_dialog,
        ]


    def _validar_y_enviar(self, e):

        patron = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        email = self.email.value.strip() if self.email.value else ""
        name = self.name.value.strip() if self.name.value else ""

        validate_name = len(name) >= 3 and not any(char.isdigit() for char in self.name.value)
        if not validate_name:
            self.error_name.value = "El nombre debe tener al menos 3 caracteres sin digitos"
            self.error_name.visible = True
            self.name.border_color = "red"
        else:
            self.error_name.visible = False
            self.name.border_color = ft.colors.BLACK

        validate_email = bool(re.match(patron, email))
        if not validate_email:
            self.error_email.value = "Formato de correo inválido"
            self.error_email.visible = True
            self.email.border_color = "red"
        else:
            self.error_email.visible = False
            self.email.border_color = "#E0D7C6"

        if validate_name and validate_email:
            new_user = User(name=name, email=email)
            self.status = self.backend_service.register_user(new_user)
            
            if self.status.get('status'):
                self.name.value = ""
                self.email.value = ""
                self.success_dialog.content.value = self.status.get('message')
                self.page.dialog = self.success_dialog
                self.success_dialog.open = True
            else:
                self.error_dialog.content.value = self.status.get('message')
                self.page.dialog = self.error_dialog
                self.error_dialog.open = True
        
        self.page.update()

    def _text_validate(self, e):

        if any(char.isdigit() for char in self.name.value):
            self.error_name.value = "Solo se permiten caracteres"
            self.error_name.visible = True
            self.name.border_color = "red"
        else:
            self.error_name.visible = False
            self.name.border_color="#E0D7C6"
        
        self.page.update()

    def _email_validate(self, e):

        self.error_email.visible = False
        self.email.border_color = "#E0D7C6"
        self.page.update()

    def _close_dialog(self, e):

        self.success_dialog.open = False
        self.error_dialog.open = False

        self.page.dialog = None
        self.page.update()
        
        if self.status.get('status'):
            self.page.clean()
            self.page.dialog = None
            self.page.update()
            self.on_success()

        