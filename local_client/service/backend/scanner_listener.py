"""
Controlador de Hardware por Inyección.
Escucha el teclado globalmente para interceptar los datos generados por un
escáner de código de barras USB antes de que el usuario haga algo.
"""

import time
import threading
from pynput import keyboard


class ScannerListener:
    def __init__(self, backend_service):
        self.backend = backend_service
        self.buffer = []
        self.ultimo_tiempo = time.time()

        # Umbral heurístico (0.3 segundos): Un humano tecleando es lento.
        # Un escáner inyecta 13 caracteres casi instantáneamente.
        self.umbral_ms = 0.3

    def _on_press(self, key):
        """Callback que se dispara por CADA tecla presionada en el sistema operativo."""
        tiempo_actual = time.time()
        diferencia_tiempo = tiempo_actual - self.ultimo_tiempo
        self.ultimo_tiempo = tiempo_actual

        # Si hubo una pausa larga, asumimos que fue un humano tecleando y
        # limpiamos el buffer para no contaminar la lectura del escáner.
        if diferencia_tiempo > self.umbral_ms:
            if self.buffer:
                self.buffer.clear()

        try:
            # El escáner siempre envía un ENTER (CRLF) cuando termina de leer.
            if key == keyboard.Key.enter:
                if self.buffer:
                    codigo_barras = "".join(self.buffer)
                    print(f"\n[Vigilante] Escáner detectado. Código: {codigo_barras}")
                    self.backend.registrar_venta(codigo_barras)
                    self.buffer.clear()

            # Capturar caracteres numéricos inyectados por el escáner
            elif hasattr(key, "char") and key.char is not None:
                self.buffer.append(key.char)

        except Exception as e:
            self.buffer.clear()

    def iniciar(self):
        """Ata el interceptor al ciclo de vida de la aplicación."""
        listener = keyboard.Listener(on_press=self._on_press)
        listener.daemon = True  # Muere automáticamente al cerrar la UI
        listener.start()
        print("[Vigilante] Activado y escuchando en las sombras...")