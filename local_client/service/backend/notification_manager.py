"""
Motor de Notificaciones Nativas (Toast)
Muestra notificaciones de escritorio en Windows para eventos importantes.
Posee un modo "silencioso" para no romper la app si se corre en Linux o macOS.
"""

import os

# Importación defensiva para que el código no falle en sistemas sin GUI (como CI/CD)
try:
    from winotify import Notification

    _WINOTIFY_DISPONIBLE = True
except ImportError:
    _WINOTIFY_DISPONIBLE = False

APP_ID = "BanAnalytics"
DURACION = "long"  # Para asegurar que el usuario vea la alerta mientras atiende


class NotificationManager:
    def __init__(self):
        if not _WINOTIFY_DISPONIBLE:
            print("[NotificationManager] winotify no detectado. Activando modo consola.")

    def notify_new_report(self, ruta_pdf: str, fecha_inicio, fecha_fin) -> bool:
        """Prepara el texto y decide si dispara un Toast nativo o un print en consola."""
        inicio_fmt = fecha_inicio.strftime("%d/%m/%Y")
        fin_fmt = fecha_fin.strftime("%d/%m/%Y")
        cuerpo = f"Vistazo a la analítica de la semana.\n({inicio_fmt} - {fin_fmt})"

        if _WINOTIFY_DISPONIBLE:
            return self._disparar_toast(ruta_pdf, cuerpo)
        else:
            return self._fallback_consola(ruta_pdf, cuerpo)

    def _disparar_toast(self, ruta_pdf: str, cuerpo: str) -> bool:
        """Construye y lanza el cuadro visual con botones interactivos."""
        try:
            ruta_absoluta = os.path.abspath(ruta_pdf)
            toast = Notification(
                app_id=APP_ID,
                title="¡Tu reporte semanal está listo!",
                msg=cuerpo,
                duration=DURACION
            )

            # Botón para abrir el visor predeterminado (Adobe Reader, Edge, etc.)
            ruta_url = "file:///" + ruta_absoluta.replace("\\", "/")
            toast.add_actions(label="Ver reporte", launch=ruta_url)

            # Botón vacío para simplemente ignorar el mensaje
            toast.add_actions(label="Descartar", launch="")

            toast.show()
            return True
        except Exception as e:
            print(f"[NotificationManager] Error al disparar Toast: {e}")
            return False

    def _fallback_consola(self, ruta_pdf: str, cuerpo: str) -> bool:
        """Solo imprime el evento si estamos en entornos tipo servidor."""
        print(f"\n[Notificación] ¡Tu reporte semanal está listo! {cuerpo}")
        return False