import flet as ft

class PrimaryButton(ft.ElevatedButton):
    def __init__(self, texto_usuario, accion_click):

        super().__init__(
            content=ft.Text(texto_usuario), 
            on_click=accion_click
        ) 
        
        self.style = ft.ButtonStyle(
            bgcolor="#C0843F",
            color="white",
            shape=ft.RoundedRectangleBorder(radius=8),
        )

        self.width = 320
        self.height = 45