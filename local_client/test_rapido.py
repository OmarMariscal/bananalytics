"""
TEST RÁPIDO - Ejecuta esto para verificar si tu venv está bien configurado
"""

import sys
import flet as ft

print(f"Python: {sys.executable}")
print(f"Flet: {ft.__version__}")
print(f"¿ft.icons existe?: {hasattr(ft, 'icons')}")
print(f"¿ft.LineChart existe?: {hasattr(ft, 'LineChart')}")
print(f"¿ft.LineChartDataPoint existe?: {hasattr(ft, 'LineChartDataPoint')}")
print(f"¿ft.Icon existe?: {hasattr(ft, 'Icon')}")

if all([
    hasattr(ft, 'icons'),
    hasattr(ft, 'LineChart'),
    hasattr(ft, 'LineChartDataPoint'),
    hasattr(ft, 'Icon')
]):
    print("\n✓ TODO ESTÁ BIEN - El problema es de VS Code Intellisense")
else:
    print("\n✗ FLET TIENE PROBLEMAS - Necesitas reinstalar")
