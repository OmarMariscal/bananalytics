"""
DIAGNÓSTICO DE PROBLEMAS CON FLET EN VS CODE
Ejecuta este script en tu terminal (dentro del venv) para identificar el problema
"""

import sys
import flet as ft

print("=" * 60)
print("DIAGNÓSTICO DE FLET")
print("=" * 60)

# 1. Verificar versión de Python
print(f"\n1. PYTHON:")
print(f"   Versión: {sys.version}")
print(f"   Ejecutable: {sys.executable}")

# 2. Verificar versión de Flet
print(f"\n2. FLET:")
print(f"   Versión: {ft.__version__}")
print(f"   Ubicación: {ft.__file__}")

# 3. Verificar atributos disponibles
print(f"\n3. ATRIBUTOS CLAVE DE FLET:")
atributos_importantes = [
    'icons',
    'LineChart',
    'LineChartDataPoint',
    'BarChart',
    'BarChartGroup',
    'PieChart',
    'Container',
    'Row',
    'Column',
    'Text',
    'Image',
    'Icon',
    'animation',
    'Animation',
]

for attr in atributos_importantes:
    tiene_attr = hasattr(ft, attr)
    estado = "✓" if tiene_attr else "✗"
    print(f"   {estado} ft.{attr}")

# 4. Verificar que ft.icons existe y tiene contenido
print(f"\n4. ICONOS DISPONIBLES:")
if hasattr(ft, 'icons'):
    print(f"   ✓ ft.icons existe")
    # Mostrar los primeros 5 iconos
    icono_list = [attr for attr in dir(ft.icons) if not attr.startswith('_')]
    print(f"   Total de iconos: {len(icono_list)}")
    print(f"   Primeros 5: {icono_list[:5]}")
else:
    print(f"   ✗ ft.icons NO existe")

# 5. Intentar crear un gráfico simple para verificar
print(f"\n5. TEST DE GRÁFICOS:")
try:
    from flet.charts import LineChart, LineChartDataPoint
    print(f"   ✓ Importación directa de LineChart funciona")
except ImportError as e:
    print(f"   ✗ Importación directa falló: {e}")

try:
    chart = ft.LineChart(
        data_series=[
            ft.LineChartData(
                data_points=[
                    ft.LineChartDataPoint(0, 1),
                    ft.LineChartDataPoint(1, 2),
                ],
            )
        ]
    )
    print(f"   ✓ Creación de LineChart directa funciona")
except Exception as e:
    print(f"   ✗ Creación de LineChart falló: {e}")

# 6. Verificar si hay type stubs
print(f"\n6. TYPE STUBS (para Intellisense):")
import os
flet_path = os.path.dirname(ft.__file__)
stub_file = os.path.join(flet_path, 'py.typed')
has_typed = os.path.exists(stub_file)
print(f"   Carpeta de Flet: {flet_path}")
print(f"   ¿Tiene archivo py.typed?: {'✓' if has_typed else '✗'}")

# Verificar si hay archivos .pyi (type hints)
pyi_files = [f for f in os.listdir(flet_path) if f.endswith('.pyi')]
print(f"   Archivos .pyi encontrados: {len(pyi_files)}")

print(f"\n" + "=" * 60)
print("FIN DEL DIAGNÓSTICO")
print("=" * 60)
