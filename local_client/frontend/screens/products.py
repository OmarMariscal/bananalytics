import flet as ft

class Products(ft.Container):
    def __init__(self, backend_service):
        super().__init__()
        
        self.backend = backend_service
        self.content = ft.Text("Contenido del Products")