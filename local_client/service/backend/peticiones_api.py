#SALE A INTERNET, ENTREGA LA INFORMACION A LA API DE ANGEL Y TRAE DE REGRESO LA RESPUESTA

import requests #Libreria que permite realizar peticiones HTTP
from shared.models.user import User

class ApiClient:
    """
    Se encarga exclusivamente de la comunicacion hacia la Nube.
    Abstrae la complejidad de la red para que el BackendService solo reciba respuestas limpias en formato diccionario.
    """
    def __init__(self):
        """
        Constructor.
        Prepara las credenciales y la ruta de destino hacia el servidor de Angel.
        """
        self.api_key = "Bananalytics-Super-Secret-Key-2026" #Llave para permitir el acceso
        self.base_url = "https://bananalytics.onrender.com/api/v1" #Direccion base de la API de Angel

    def check_health(self):
        url_chequeo = f"{self.base_url}/health"

        try:
            respuesta = requests.get(url_chequeo, timeout=3)

            if respuesta.status_code == 200:
                datos = respuesta.json()

                servidor_listo = datos.get("status") == "online"
                db_lista = datos.get("base_datos") == "conectada"

                if servidor_listo and db_lista:
                    return True
                else:
                    print(f"Servidor en linea pero la base de datos presenta problemas: {datos}")
                    return False

            print(f"El servidor tiene problemas para la conexion (Status: {respuesta.status_code})")

        except requests.exceptions.RequestException:
            print("Imposible conectar. Revisar la conexion o el estado del servidor.")
            return False


    #Rogelio pasa el usuario y este metodo lo envia
    def register_user(self, user: User) -> dict:
        """
        Flujo de Alta de Sucursal.
        Empaqueta los datos del usuario local y solicita a la nube un 'id_negocio' oficial.
        """
        #Construye la direccion completa a la que tiene que ir el paquete
        url_registro = f"{self.base_url}/business/register"
        #El paquete JSON que se entrega a Angel
        payload = {
            "name": user.name,
            "email": user.email,
            "city": "Guadalajra, Jalisco",
            "lat": 20.6596,
            "lng": -103.3496
        }
        headers = {
                    "X-API-Key": self.api_key,
                   "Content-Type": "application/json"
                   } #Etiquetas fuera de la caja

        try:
            #Se hace peticion POST, pasamos la URL, el JSON, las etiquetas. Si el servidor no responde en 10 segundos, se rinde y regresa
            response = requests.post(url_registro, json=payload, headers=headers, timeout=10)
            #La respuesta es una confirmacion de recibo
            data = response.json()

            #Si todo salio bien, devolvemos un diccionario de exito al BackendService. Si no, devolvemos el error que el servidor haya enviado
            if response.status_code == 200 and data.get("status") == "exito":
                return {"status": "exito", "mensaje": "Registro completado", "id_negocio": data.get("id_negocio", "1")}
            return {"status": data.get("status", "fail"), "mensaje": data.get("mensaje", "Error conocido")}


        except requests.exceptions.RequestException:
            return {"status": "fail", "mensaje": "No se pudo conectar con el servidor"}


    #Traemos de la API toda la informacion que Rogi ocupe para el dashboard
    def get_dashboard_data(self, store_id: str) -> dict:
<<<<<<< Updated upstream
        
    #Trae todas las predicciones, alertas y resumenes de ventas para rellenar
        #la pantalla principal de la aplicacion.
        
=======

    #Trae todas las predicciones, alertas y resumenes de ventas para rellenar
        #la pantalla principal de la aplicacion.

>>>>>>> Stashed changes
        url = f"{self.base_url}/business/{store_id}/predictions" #Ruta con el id de la tienda inyectado para identificar que datos enviar
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            respuesta = requests.get(url, headers=headers, timeout=10)
            if respuesta.status_code == 200:
                return respuesta.json()
            return {} #Si Angel manda error, devolvemos un lienzo en blanco para no crashear
        except requests.exceptions.RequestException:
            return {}

    #Viaja a la API para traer toda la informacion de un solo producto
    def get_product_data(self, store_id: str, barcode: str) -> dict:
<<<<<<< Updated upstream
        
        #Viaja a la API para traer el historial detallado y las predicciones
        #de un unico producto escaneado.
        
=======

        #Viaja a la API para traer el historial detallado y las predicciones
        #de un unico producto escaneado.

>>>>>>> Stashed changes
        url = f"{self.base_url}/business/{store_id}/{barcode}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            respuesta = requests.get(url, headers=headers, timeout=10)
            if respuesta.status_code == 200:
                return respuesta.json()
            return {}
        except requests.exceptions.RequestException:
            return {}



