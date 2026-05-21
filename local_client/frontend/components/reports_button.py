import flet as ft
import os
import platform
import subprocess
import traceback

class ReportsFolderButton(ft.Container):
    def __init__(self, page):
        super().__init__()
        self.page = page
        self.folder_path = os.path.abspath("data/reports")
        
        self.width = 45
        self.height = 45
        self.alignment = ft.alignment.center
        
        self.tooltip = "Ver reportes semanales en PDF"
        
        self.content = ft.IconButton(
            icon=ft.icons.FOLDER_OPEN_OUTLINED,
            icon_color="#8D7A66",
            on_click=self._handle_click,
            style=ft.ButtonStyle(
                padding=0
            )
        )

    def _handle_click(self, e):
        try:
            # VALIDACIÓN 1: ¿La carpeta no existe?
            if not os.path.exists(self.folder_path):
                self._show_alert(
                    title="No hay reportes actualmente", 
                    message="La carpeta de reportes semanales no existe en el sistema."
                )
                return
            
            # VALIDACIÓN 2: ¿La carpeta existe pero está vacía?
            if not os.listdir(self.folder_path):
                self._show_alert(
                    title="No hay reportes actualmente", 
                    message="La carpeta de reportes existe, pero se encuentra completamente vacía."
                )
                return

            # ÉXITO: Abre al frente la carpeta
            self._open_system_folder()

        except Exception as error:
            print("🚨 Error al intentar inspeccionar la carpeta de reportes:")
            print(traceback.format_exc())
            self._show_alert(
                title="Error de acceso", 
                message=f"No se pudo acceder a la ruta de almacenamiento. Detalle técnico: {error}"
            )

    def _show_alert(self, title, message):
        alert = ft.AlertDialog(
            title=ft.Text(title, weight="bold", color=ft.colors.ON_SURFACE),
            content=ft.Text(message, color=ft.colors.ON_SURFACE),
            actions=[
                ft.TextButton("Entendido", on_click=lambda e: self._close_dialog(alert))
            ]
        )
        self.page.dialog = alert
        alert.open = True
        self.page.update()

    def _close_dialog(self, alert):
        alert.open = False
        self.page.update()

    def _open_system_folder(self):
        sistema_operativo = platform.system()
        if sistema_operativo == "Windows":
            subprocess.Popen(["explorer", self.folder_path])
        elif sistema_operativo == "Darwin":  # macOS
            subprocess.Popen(["open", self.folder_path])
        else:  # Linux
            subprocess.Popen(["xdg-open", self.folder_path])