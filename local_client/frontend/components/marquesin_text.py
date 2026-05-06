import flet as ft
import asyncio

class TextoMarquesina(ft.Container):
    def __init__(self, texto, ancho_max, size_text, color):
        super().__init__()
        self.width = ancho_max
        self.clip_behavior = ft.ClipBehavior.ANTI_ALIAS
        self.texto_plano = texto
        
        # El control de texto
        self.texto_control = ft.Text(
            self.texto_plano,
            size=size_text,
            weight="bold",
            color=color,
            no_wrap=True,
        )
        
        # Contenedor interno que se moverá
        self.contenedor_movil = ft.Container(
            width=float("inf"), 
            animate_offset=ft.Animation(1000, ft.AnimationCurve.EASE_IN_OUT),
            offset=ft.Offset(0, 0),
            content=ft.Row([self.texto_control], tight=True)
        )
        
        self.content = self.contenedor_movil
        self.corriendo = False

    def did_mount(self):
        # Estimamos el ancho del texto (aprox 16px por caracter en Bold size 28)
        ancho_estimado_texto = len(self.texto_plano) * 16
        
        # CONDICIÓN 2: Solo si el texto es más ancho que el cajón, animamos
        if ancho_estimado_texto > self.width:
            self.corriendo = True
            self.page.run_task(self._iniciar_marquesina_rebote)

    def will_unmount(self):
        self.corriendo = False

    async def _iniciar_marquesina_rebote(self):
        await asyncio.sleep(1.5) # Pausa inicial
        
        # Calculamos cuánto debe desplazarse para mostrar el final
        # El offset se basa en fracciones del tamaño del componente hijo.
        # Un desplazamiento de -0.5 suele ser suficiente para nombres largos.
        # Ajustamos dinámicamente según el largo:
        proporcion_desplazamiento = (len(self.texto_plano) * 16 - self.width) / (len(self.texto_plano) * 16)
        # Forzamos un valor negativo para ir a la izquierda
        target_offset = -abs(proporcion_desplazamiento) - 0.1 

        hacia_izquierda = True

        while self.corriendo:
            if hacia_izquierda:
                # 1. CONDICIÓN 1: Mover a la izquierda (Fin del texto)
                self.contenedor_movil.animate_offset = ft.Animation(3000, ft.AnimationCurve.EASE_IN_OUT)
                self.contenedor_movil.offset = ft.Offset(target_offset, 0)
            else:
                # Regresar a la derecha (Inicio del texto)
                self.contenedor_movil.animate_offset = ft.Animation(3000, ft.AnimationCurve.EASE_IN_OUT)
                self.contenedor_movil.offset = ft.Offset(0, 0)

            try:
                await self.contenedor_movil.update_async()
            except:
                break
            
            # Esperar a que termine la animación (3s) + pausa en el extremo (2s)
            await asyncio.sleep(5)
            
            # Cambiamos de dirección
            hacia_izquierda = not hacia_izquierda