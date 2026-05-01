import time
import threading
from pynput import keyboard

class ScannerListener:
    """
    Se ejecuta en segundo plano esperando seniales del escaner de codigo de barras USB.
    Usa telemetria de tiempo para distinguir entre un humano escribiendo en el
    teclado y un escaner disparando datos a alta velocidad.
    """
    def __init__(self, backend_service):
        """
        Constructor.
        Prepara la recoleccion y define las reglas de velocidad.
        """
        #Referencia al Service para avisarle cuando haya un escaneo exitoso
        self.backend = backend_service
        self.buffer = []
        self.ultimo_tiempo = time.time()
        #Si pasan as de 0.3 segundos entre teclas, asumimos que es un humano y cancelamos.
        self.umbral_ms = 0.3

    def _on_press(self, key):
        """
        Evento disparado por el sistema operativo cada vez que se presiona CUALQUIER tecla
        Filtra, acumula y decide cuando entregar el codigo final.
        """
        tiempo_actual = time.time()
        diferencia_tiempo = tiempo_actual - self.ultimo_tiempo
        self.ultimo_tiempo = tiempo_actual

        #Filtro, si tardas mucho, no es el escaner
        if diferencia_tiempo > self.umbral_ms:
            if len(self.buffer) > 0:                self.buffer.clear()

        try:
            #El escaner USB siempre manda un 'Enter' a terminar de leer
            if key == keyboard.Key.enter:
                if len(self.buffer) > 0:
                    #Se unen todas las teclas guardadas en un solo texto.
                    codigo_barras = "".join(self.buffer)
                    print(f"\n🎯 [Vigilante] ¡Escáner detectado! Código interceptado: {codigo_barras}")
                    #Pasamos el codigo al Service para que lo guarde
                    self.backend.registrar_venta(codigo_barras)
                    #Vaciamos el buffer para la siguiente compra
                    self.buffer.clear()

            elif hasattr(key, 'char') and key.char is not None:
                self.buffer.append(key.char)
                #print(f"📥 [Debug] Guardado: '{key.char}'. Bolsita actual: {self.buffer}")

        except Exception as e:
            print(f"⚠️ [Vigilante] Error al procesar tecla: {e}")
            self.buffer.clear()

    def iniciar(self):
        """
        Se llama al scanner y lo pone a trabajar en un hilo invisible.
        De esta forma, se puede escuchar las teclas en todo momento sin importar
        que pantalla de la interfaz grafica este abierta.
        """
        listener = keyboard.Listener(on_press=self._on_press)
        listener.daemon = True
        listener.start()
        print("[Vigilante] Activado y escuchando en las sombras...")


