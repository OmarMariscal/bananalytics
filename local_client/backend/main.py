from fastapi import FastAPI
from local_client.backend.sync.sync import PaqueteVentasSchema
from local_client.backend.db.sqlite_manager import crear_tablas, obtener_conexion
from local_client.backend.sync.sync import sincronizacion_nocturna, procesar_cola_pendientes
import asyncio

app = FastAPI()

async def daemon_sincronizacion():
    await asyncio.sleep(5)

    while True:
        await asyncio.to_thread(procesar_cola_pendientes)
        await asyncio.sleep(1800)

@app.on_event("startup")
async def arranque():
    crear_tablas()
    print("Base de datos local lista")

    asyncio.create_task(daemon_sincronizacion())
    print("Daemon de sincronizacion offline iniciado en segundo plano")

@app.get("/health")
def health_check():
    return{
        "status": "online",
        "version": "1.0",
        "base_datos": "sin conectar(por ahora)"
    }

@app.post("/api/v1/ventas/sync")
def sincronizar_ventas(paquete: PaqueteVentasSchema):
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    total_productos = 0
    for transaccion in paquete.sales:
        for producto in transaccion.products:
            cursor.execute("""
            INSERT INTO sales_now (barcode, time, amount, temperature, weather_resume)
            VALUES (?, ?, ?, ?, ?)
            """, (producto.barcode, transaccion.time, producto.amount, transaccion.temperature, transaccion.weather_resume))
            total_productos += 1

    conexion.commit()
    conexion.close()
    return {
        "status": "exito",
        "ventas_recibidas": len(paquete.sales),
        "productos_guardados": total_productos,
        "id_store": paquete.id_store
    }

@app.get("/api/v1/ventas/ver")
def ver_ventas():
    conexion = obtener_conexion()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM sales_now")
    filas = cursor.fetchall()
    conexion.close()

    resultado = []
    for fila in filas:
        resultado.append({
            "id": fila[0],
            "barcode": fila[1],
            "time": fila[2],
            "amount": fila[3],
            "temperature": fila[4],
            "weather_resume": fila[5]
        })
    return {"total": len(resultado), "ventas": resultado}

@app.get("/api/v1/test/sync")
def test_sync():
    try:
        sincronizacion_nocturna()
        return {"mensaje": "Sincronización ejecutada, revisa la terminal"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/v1/test/limpiar")
def limpiar_sqlite():

    conexion = obtener_conexion()
    cursor = conexion.cursor()


    cursor.execute("DELETE FROM sales_now")


    cursor.execute("DELETE FROM sqlite_sequence WHERE name='sales_now'")


    conexion.commit()
    conexion.close()
    return {"mensaje": "SQLite limpiado correctamente"}

@app.post("/api/v1/simulador-nube/sync")
def simulador_angel(paquete: dict):
    print(f"[NUBE SIMULADA] ¡Paquete de la tienda recibido con éxito!")
    return {"status": "success", "mensaje": "Datos procesados en la nube"}