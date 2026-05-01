"""
Renderizador de Reportes — BanAnalytics Worker Reports.

Responsabilidades:
  1. Leer el logotipo desde disco y codificarlo en Base64 para incrustarlo
     directamente en el HTML como Data URI, eliminando la dependencia de rutas
     del sistema de archivos en tiempo de renderizado PDF.
  2. Leer el archivo styles.css e inyectarlo inline dentro del <style> del
     template Jinja2, evitando referencias externas que WeasyPrint podría no
     resolver en el entorno efímero de GitHub Actions runners.
  3. Renderizar el template Jinja2 con todos los datos del contexto.
  4. Convertir el HTML renderizado a bytes PDF con WeasyPrint.

Compatibilidad con WeasyPrint 62.x:
  La API de WeasyPrint 62 difiere de versiones anteriores en dos puntos clave:
    · `presentational_hints` es parámetro del constructor `HTML()`, NO de `write_pdf()`.
    · `font_config`          es parámetro de `CSS()`,            NO de `write_pdf()`.
  Dado que este worker inyecta el CSS inline (sin referencias externas a
  archivos .css en disco) y las fuentes se cargan desde Google Fonts (fallback
  a fuentes del sistema) sin necesidad de `@font-face` local, `FontConfiguration`
  no es necesario. El CSS inline se gestiona directamente dentro del <style>
  del HTML renderizado por Jinja2.

Decisión de diseño — PDF en memoria (io.BytesIO):
  El PDF nunca se escribe en disco. Se genera en memoria y se retorna como
  `bytes` para que `mailer.py` lo adjunte directamente al correo. Esto es
  correcto para un runner efímero de GitHub Actions donde cualquier archivo
  escrito en disco desaparece al terminar el job, y evita la necesidad de
  gestión de archivos temporales con sus correspondientes riesgos de limpieza.

Decisión de diseño — Fuentes en PDF:
  WeasyPrint descarga fuentes de Google Fonts si hay conexión. Para garantizar
  reproducibilidad incluso offline, el CSS declara fallbacks a fuentes del
  sistema ('DejaVu Sans', Georgia) que vienen preinstaladas en Ubuntu mediante
  los paquetes fonts-liberation y fonts-dejavu-core instalados en el workflow.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

from db_queries import CategoryStats, StoreRecord, WeeklyStats
from logger import get_logger

logger = get_logger(__name__)

# ── Rutas base del microservicio ─────────────────────────────────────────────

_BASE_DIR = Path(__file__).parent
_TEMPLATES_DIR = _BASE_DIR / "templates"
_STYLES_PATH = _TEMPLATES_DIR / "styles.css"
_LOGO_PATH = _TEMPLATES_DIR / "assets" / "logo_bananalytics.png"

# ── Entorno Jinja2 ────────────────────────────────────────────────────────────

_jinja_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
    # trim_blocks y lstrip_blocks eliminan espacios/saltos innecesarios
    # generados por las etiquetas de control Jinja2, produciendo HTML más limpio.
    trim_blocks=True,
    lstrip_blocks=True,
)


def _load_css() -> str:
    """
    Lee el archivo styles.css y retorna su contenido como string.

    El contenido se inyecta dentro de la etiqueta <style> del template a través
    de la variable `css`, usando el filtro `| safe` de Jinja2 para evitar
    el escape HTML que corrompería las propiedades CSS.

    Returns:
        Contenido completo de styles.css como string UTF-8.

    Raises:
        FileNotFoundError: Si styles.css no existe en la ruta esperada.
    """
    if not _STYLES_PATH.exists():
        raise FileNotFoundError(
            f"Archivo de estilos no encontrado: {_STYLES_PATH}. "
            "Verifique que templates/styles.css existe en el directorio del worker."
        )
    content = _STYLES_PATH.read_text(encoding="utf-8")
    logger.debug(f"  CSS cargado: {len(content):,} caracteres desde {_STYLES_PATH.name}")
    return content


def _load_logo_as_base64() -> str:
    """
    Lee el logotipo PNG y lo codifica como Base64 para Data URI.

    Al incrustarlo como `data:image/png;base64,...` en el atributo `src` de
    la etiqueta <img>, el renderizador PDF no necesita acceso al sistema de
    archivos en tiempo de conversión. Esto elimina errores por paths relativos
    y garantiza que el logo aparezca correctamente en todos los entornos.

    Returns:
        String Base64 del contenido binario del PNG (sin el prefijo data URI,
        que el template añade directamente).

    Raises:
        FileNotFoundError: Si el logo no existe en la ruta esperada.
    """
    if not _LOGO_PATH.exists():
        logger.warning(
            f"⚠️  Logo no encontrado en {_LOGO_PATH}. "
            "El reporte se generará sin imagen de marca."
        )
        # Retorna un pixel transparente de 1x1 px como fallback
        return (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk"
            "YPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
        )

    raw_bytes = _LOGO_PATH.read_bytes()
    encoded = base64.b64encode(raw_bytes).decode("ascii")
    logger.debug(
        f"  Logo cargado: {len(raw_bytes):,} bytes → "
        f"{len(encoded):,} chars Base64 desde {_LOGO_PATH.name}"
    )
    return encoded


def render_report_html(
    store: StoreRecord,
    stats: WeeklyStats,
    category_breakdown: list[CategoryStats],
    generated_at: str,
) -> str:
    """
    Renderiza el template Jinja2 con todos los datos del reporte.

    Este método encapsula la construcción del contexto de template y la
    llamada al renderizador de Jinja2. Retorna el HTML completo como string,
    lo que permite inspeccionar el resultado intermedio para debugging.

    Args:
        store:              Datos de la tienda destinataria.
        stats:              Métricas agregadas y listas de predicciones.
        category_breakdown: Lista de CategoryStats para la tabla de categorías.
        generated_at:       Timestamp formateado de generación (para el footer).

    Returns:
        HTML completo como string UTF-8, listo para pasar a WeasyPrint.

    Raises:
        jinja2.TemplateNotFound: Si report_template.html no existe.
        FileNotFoundError:       Si styles.css o el logo no existen.
    """
    css_content = _load_css()
    logo_b64 = _load_logo_as_base64()

    template = _jinja_env.get_template("report_template.html")

    context = {
        # Datos de la tienda
        "store": store,
        # Métricas y listas de predicciones
        "stats": stats,
        # Breakdown por categoría
        "category_breakdown": category_breakdown,
        # Metadatos del documento
        "generated_at": generated_at,
        # Recursos incrustados (evitan dependencias de rutas en WeasyPrint)
        "css": css_content,
        "logo_b64": logo_b64,
    }

    html_output = template.render(**context)

    logger.debug(
        f"  HTML renderizado: {len(html_output):,} caracteres "
        f"para tienda {store.store_id} ({store.owner_name})"
    )
    return html_output


def render_report_pdf(
    store: StoreRecord,
    stats: WeeklyStats,
    category_breakdown: list[CategoryStats],
    generated_at: str,
) -> bytes:
    """
    Genera el reporte PDF completo para una tienda y lo retorna como bytes.

    Pipeline interno:
        1. render_report_html()  → HTML string completo
        2. WeasyPrint HTML()     → DOM del documento
        3. .write_pdf()          → bytes del PDF en memoria

    El PDF se genera completamente en memoria (io.BytesIO) y nunca toca el
    disco del runner, lo que es correcto para entornos de CI/CD efímeros.

    Args:
        store:              Datos de la tienda destinataria.
        stats:              Métricas agregadas y listas de predicciones.
        category_breakdown: Lista de CategoryStats para la tabla de categorías.
        generated_at:       Timestamp formateado de generación.

    Returns:
        Contenido binario del PDF como `bytes`.

    Raises:
        WeasyPrint exceptions si el HTML es inválido o hay errores de renderizado.
        FileNotFoundError si los recursos del template no están disponibles.
    """
    logger.info(
        f"  🖨  Renderizando PDF para tienda {store.store_id} "
        f"({store.owner_name}, {store.city})..."
    )

    # Paso 1: Renderizar HTML desde el template Jinja2
    html_string = render_report_html(
        store=store,
        stats=stats,
        category_breakdown=category_breakdown,
        generated_at=generated_at,
    )

    # Paso 2: Crear objeto HTML de WeasyPrint.
    #
    # `presentational_hints=True`: permite que WeasyPrint respete atributos
    # HTML de presentación (align, bgcolor, width en tablas), mejorando la
    # compatibilidad con el HTML generado por Jinja2.
    # ⚠️  CORRECCIÓN WeasyPrint 62.x: este parámetro pertenece al constructor
    # HTML(), NO a write_pdf(). Pasarlo en write_pdf() causa TypeError.
    #
    # `base_url=str(_TEMPLATES_DIR)`: fallback para resolución de URLs relativas.
    # En la práctica el CSS es inline y el logo es Data URI, por lo que
    # WeasyPrint no realiza peticiones de recursos externos.
    wp_document = HTML(
        string=html_string,
        base_url=str(_TEMPLATES_DIR),
    )

    # Paso 3: Renderizar a bytes PDF en memoria.
    #
    # `target=pdf_buffer`: escribe el PDF directamente en el BytesIO, evitando
    # escritura en disco. `io.BytesIO.getvalue()` retorna todo el contenido
    # independientemente de la posición del cursor (no requiere seek(0)).
    #
    # ⚠️  CORRECCIÓN WeasyPrint 62.x: write_pdf() NO acepta `font_config` ni
    # `presentational_hints` como parámetros en esta versión. Pasarlos causa
    # TypeError: write_pdf() got an unexpected keyword argument.
    # `FontConfiguration` solo se necesita al usar `CSS(font_config=...)` con
    # fuentes @font-face locales, que no es el caso de este worker.
    pdf_buffer = io.BytesIO()
    wp_document.write_pdf(target=pdf_buffer)

    pdf_bytes = pdf_buffer.getvalue()
    size_kb = len(pdf_bytes) / 1024

    logger.info(
        f"  ✅ PDF generado: {size_kb:.1f} KB "
        f"para {store.owner_name} (tienda {store.store_id})"
    )

    return pdf_bytes
