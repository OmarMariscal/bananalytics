import flet as ft

class TextoMarquesina(ft.Container):
    def __init__(self, texto, ancho_max, size_text, color):
        super().__init__()
        
        self.content = ft.Text(
            value=texto,
            size=size_text,
            weight="bold",
            color=color,
            no_wrap=True,
            overflow=ft.TextOverflow.ELLIPSIS,
            tooltip=texto
        )
        self.width = ancho_max