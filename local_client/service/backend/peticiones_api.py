#SALE A INTERNET, ENTREGA LA INFORMACION A LA API DE ANGEL Y TRAE DE REGRESO LA RESPUESTA

import requests #Libreria que permite realizar peticiones HTTP
from shared.models.user import User

class ApiClient:
    def __init__(self):
        self.api_key = "tu_clave_secreta" #Llave para permitir el acceso
        self.base_url = "http://127.0.0.1:8000/api/v1" #Direccion base de la API de Angel

    #Rogelio pasa el usuario y este metodo lo envia
    def register_user(self, user: User) -> dict:
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
        headers = {"X-API-Key": self.api_key} #Etiquetas fuera de la caja

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