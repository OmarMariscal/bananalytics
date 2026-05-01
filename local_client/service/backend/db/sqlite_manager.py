import sqlite3
from datetime import datetime

class SQLiteManager:
    """
    Administrador de la Base de Datos Local
    Principal responsabilidad es recibir los
    escaneos en tiempo real del escaner y almacenarlos
    de forma segura en el disco duro hasta que el Daemon despierte para empaquetarlos y enviarlos a la nube
    """
    def __init__(self):
        """
        Constructor de la Boveda.
        Establece el nombre del archivo fisico de la base de datos y garantiza
        que la estructura interna (tablas) exista desde el milisegundo cero de ejecucion.
        """
        #Define el nombre del archivo que se va a crear
        self.tienda_db = "tienda.db"
        #Cada vez que el programa arranca, verifica que las tablas existan
        self.crear_tablas()

    def obtener_conexion(self):
        #Abre un puente de comunicacion con el archivo SQLite
        #Abre el archivo de la base de datos
        return sqlite3.connect(self.tienda_db)

    def crear_tablas(self):
        """
        Define el "Esquema" (Schema) de la base de datos local,
        Aqui se dictan las reglas estrictas de como se guarda una venta cruda.
        :return:
        """
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        #Definimos que columnas tendra la tabla de ventas

        #Usamos IF NOT EXISTS para que no sobreescriba los datos si la app se reinicia.
        #Decision Arquitectonica: 'time' se guarda completo (YYYY-MM-DD HH:MM:SS)
        #para no perder trazabilidad. El SynncDaemon se encargara de cortarlo
        #y generar las "cubetas" de 30 minutos mas tarde.
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
        """
        Consulta rapida de estadisticas para la interfaz de usuario

        Returns:
            dict: Un diccionario con el total de articulos escaneados hoy, listo
            para inyectarse directamente en los graficos del Dashboard de Flet.

        """
        conexion = self.obtener_conexion()
        cursor = conexion.cursor()
        cursor.execute("SELECT SUM(amount) FROM sales_now") #Orden SQL que suma todos los valores de la columna de "cantidad"
        resultado = cursor.fetchone() #Trae el resultado
        conexion.close()

        total_escaneos = resultado[0] if resultado[0] is not None else 0
        return {"total_scans_today": total_escaneos}

    def guardar_venta_local(self, codigo_barras: str) -> bool:
        """
        Punto de entrada de altisima velocidad para nuevos escaneos.
        Este metodo es llamado exclusivamente por el pynput
        cada vez que la pistola lee un codgio de barras fisico.

        Args:
            codigo_barras (str): El codigo numerico capturado por el hardware.

        Returns:
            bool: True si la venta se persistio con exito, False si hubo un error de disco.
        """
        try:
            conexion = self.obtener_conexion()
            cursor = conexion.cursor()

            #Sellamos el registro con la hora exacta del sistema operativo.
            fecha_hora_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            #Regla de Negocio: Como el hardware solo lee codigo de barras,
            #asumimos que paso "1" unidad fisica por la caja registradora.
            cantidad_o_precio = 1

            #Insercion parametrizada (?, ?, ?) para evitar ataques de Inyeccion SQL
            #(Una practica fundamental de ciberseguridad, incluso en bases locales).
            cursor.execute(
                """
                INSERT INTO sales_now (barcode, time, amount) 
                VALUES (?, ?, ?)
                """,
                (codigo_barras, fecha_hora_actual, cantidad_o_precio)
            )

            conexion.commit()
            conexion.close()

            return True

        except Exception as e:
            #Si falla el disco o el archivo esta ocupado, registramos el error
            #en la terminal sin hacer que toda la interfaz visual colapse.
            print(f"❌ [SQLiteManager] Error crítico de base de datos: {e}")
            return False


