import sqlite3

tienda_db = "tienda.db"

def obtener_conexion():
    conexion = sqlite3.connect(tienda_db)
    return conexion

def crear_tablas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_now (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        barcode TEXT NOT NULL,
        time TEXT NOT NULL,
        amount INTEGER NOT NULL,
        )
    """)

    conexion.commit()
    conexion.close()