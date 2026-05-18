import flet as ft
import asyncio

class TextoMarquesina(ft.Container):
    def __init__(self, texto, ancho_max, size_text, color):
        super().__init__()
        self.texto = texto
        self.ancho_max = ancho_max
        self.size_text = size_text
        
        # Ajuste de ancho para RobotoMono
        self.ANCHO_CARACTER = size_text * 0.53
        self.ancho_total_texto = len(self.texto) * self.ANCHO_CARACTER
        
        self.width = ancho_max
        self.clip_behavior = ft.ClipBehavior.HARD_EDGE
        self.alignment = ft.alignment.center_left
        
        self.running = False
        self.task = None 

        self.text_control = ft.Text(
            value=self.texto,
            size=self.size_text,
            color=color,
            weight="bold",
            font_family="RobotoMono",
            no_wrap=True,
        )
        
        self.inner_container = ft.Container(
            content=self.text_control,
            left=0,
            animate_position=ft.Animation(2000, ft.AnimationCurve.EASE_IN_OUT),
        )
        
        self.content = ft.Stack(
            controls=[self.inner_container],
            height=size_text + 10,
        )

    def did_mount(self):
        if self.page and self.ancho_total_texto > self.ancho_max:
            self.running = True
            self.task = self.page.run_task(self.animate_text)

    def will_unmount(self):
        # IMPORTANTE: Solo bajamos el interruptor. 
        # NO llamamos a self.task.cancel() para evitar que Flet se rompa internamente.
        self.running = False

    async def animate_text(self):
        try:
            distancia = -(self.ancho_total_texto - self.ancho_max + 10)
            while self.running:
                await asyncio.sleep(3)
                if not self.running or not self.page:
                    break
                self.inner_container.left = distancia
                self.update()
                await asyncio.sleep(3)
                if not self.running or not self.page:
                    break
                self.inner_container.left = 0
                self.update()
        except asyncio.CancelledError:
            # La tarea fue cancelada por Flet → no pasa nada
            pass
        except Exception:
            pass
        finally:
            self.task = None
