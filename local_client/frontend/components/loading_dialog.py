import flet as ft

class LoadingDialog(ft.AlertDialog):
    def __init__(self, mensaje):
        super().__init__()
        self.modal = True 
        self.bgcolor = ft.colors.ON_SURFACE_VARIANT
        self.on_dismiss = lambda e: None
        self.texto_mensaje = ft.Text(mensaje, size=20, color=ft.colors.ON_SURFACE, weight="bold")
        
        self.content = ft.Container(
            padding=ft.padding.all(10),
            content=ft.Row(
                controls=[
                    ft.ProgressRing(color="#C0843F", stroke_width=3, width=30, height=30),
                    self.texto_mensaje
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=20,
                tight=True
            )
        )

    def actualizar_mensaje(self, nuevo_mensaje):
        self.texto_mensaje.value = nuevo_mensaje
        if self.page:
            self.update()