import sqlite3

class SQLiteManager:
    def __init__(self):
        #Define el nombre del archivo que se va a crear
        self.tienda_db = "tienda.db"
        #Cada vez que el programa arranca, verifica que las tablas existan
        self.crear_tablas()

    def obtener_conexion(self):
        #Abre el archivo de la base de datos
        return sqlite3.connect(self.tienda_db)

    def crear_tablas(self):
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        #Definimos que columnas tendra la tabla de ventas

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales_now(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT NOT NULL,
            time TEXT NOT NULL,
            amount INTEGER NOT NULL
        )
        """)
        conexion.commit()
        conexion.close()
        print("Base de datos local lista")

    def get_today_stats(self) -> dict:
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT SUM(amount) FROM sales_now") #Orden SQL que suma todos los valores de la columna de "cantidad"
        resultado = cursor.fetchone() #Trae el resultado
        conexion.close()

        total_escaneos = resultado[0] if resultado[0] is not None else 0
        return {"total_scans_today": total_escaneos}


