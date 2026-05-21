import threading
import flet as ft

class ShowError(ft.AlertDialog):
    def __init__(self, page, title, menssage, usar_evento=False):
        super().__init__()
        self.page = page
        
        self.click_event = threading.Event() if usar_evento else None

        def close_dlg(e):
            self.page.close(self)
            
            if self.click_event:
                self.click_event.set()

        self.modal = True  
        self.title = ft.Text(title, color=ft.colors.ON_SURFACE, weight="bold")
        self.content = ft.Text(menssage, color=ft.colors.ON_SURFACE, weight="bold") 
        self.actions = [ft.TextButton("Entendido", on_click=close_dlg)]
        self.bgcolor = ft.colors.ON_SURFACE_VARIANT