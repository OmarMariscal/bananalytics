"""
Administrador de la Base de Datos Local.
Responsabilidad principal: recibir escaneos en tiempo real a máxima velocidad
y almacenarlos de forma segura en disco hasta que el SyncDaemon los empaquete.
"""

import sqlite3
from datetime import datetime

class SQLiteManager:
    def __init__(self):
        self.tienda_db = "tienda.db"
        self.crear_tablas()

    def obtener_conexion(self) -> sqlite3.Connection:
        # check_same_thread=False permite que múltiples hilos (como el listener del 
        # escáner y el daemon de sincronización) accedan a la BD sin crashear.
        return sqlite3.connect(self.tienda_db, check_same_thread=False)

    def crear_tablas(self):
        """
        Define el esquema local. La columna 'time' se guarda completa para 
        no perder trazabilidad; el SyncDaemon se encarga luego de agrupar por bloques.
        """
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_now (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                barcode TEXT    NOT NULL,
                time    TEXT    NOT NULL,
                amount  INTEGER NOT NULL
            )
        """)
        conexion.commit()
        conexion.close()
        print("[SQLiteManager] Base de datos local lista.")

    def get_today_stats(self) -> dict:
        """Devuelve el total de artículos escaneados hoy para pintar el Dashboard."""
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT SUM(amount) FROM sales_now")
        resultado = cursor.fetchone()
        conexion.close()

        total_escaneos = resultado[0] if resultado[0] is not None else 0
        return {"total_scans_today": total_escaneos}

    def guardar_venta_local(self, codigo_barras: str) -> bool:
        """
        Punto de entrada de altísima velocidad. 
        El ScannerListener invoca esto repetidas veces por segundo si es necesario.
        """
        try:
            conexion = self.obtener_conexion()
            cursor = conexion.cursor()
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cantidad = 1 # Se asume 1 unidad por cada escaneo físico

            cursor.execute(
                "INSERT INTO sales_now (barcode, time, amount) VALUES (?, ?, ?)",
                (codigo_barras, fecha_hora_actual, cantidad)
            )
            conexion.commit()
            conexion.close()
            return True

        except Exception as e:
            print(f"[SQLiteManager] Error crítico de base de datos: {e}")
            return False