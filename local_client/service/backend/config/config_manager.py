#LEER Y ESCRIBIR EL ARCHIVO SETTINGS.JSON

import os
import json
from datetime import date
from shared.models.user import User
from shared.models.info_config import ConfigStats


class ConfigManager:
    """
    Administrador de Configuraciones Locales.
    Maneja el estado persistente de la aplicacion en el disco duro.
    Decide si la aplicacion debe comportarse como nueva o si ya tiene
    una identidad confirmada por la nube.
    """
    #Definir el nombre del archivo
    def __init__(self):
        """
        Constructor.
        Establece y asegura la existencia de la carpeta 'Conf' y el archivo 'settings.json'.
        """
        self.carpeta_conf = "Conf"
        #exist_ok=True previene que el programa falle si la carpeta ya fue creada
        os.makedirs(self.carpeta_conf, exist_ok=True)
        self.archivo_config = os.path.join(self.carpeta_conf, "settings.json")

    #Validar si es el primer inicio al buscar el ARCHIVO_CONFIG
    def is_first_start(self) -> bool:
        """
        El Gatekeeper de la Interfaz.
        Flet llama a este metodo para decidir si muestra la pantalla de Registro o el Dashboard.

        Returns:
            bool: True si es una instalacion virgen o si los datos se corrompieron.
                    False si la tienda ya esta registrada y configurada.
        """
        if not os.path.exists(self.archivo_config):
            return True #Si no existe,el usuario nunca se ha registrado, por lo tanto devuelve True
        try:
            with open(self.archivo_config, "r") as f:
                config = json.load(f)
                return not config.get("system", {}).get("first_launch_completed", False) #Si existe el archivo creado, pero el valor es False, es primer inicio
        except (json.JSONDecodeError, KeyError):
            return True

    def create_configurations(self, user: User, id_store: str) -> bool:
        """
        Genera la "Cedula de Identidad" de la tienda.
        Se ejecuta UNICAMENTE despues de que la API aprueba el registro
        y nos devuelve un ID de tienda valido.
        """
        #Organiza los datos como los tenemos definidos
        config_data = {
            #Rutas tecnicas
            "system": {
                "first_launch_completed": True,
                "local_db_path": "./tienda.db"
            },
            #Datos del dueno
            "store_profile": {
                "id_store": str(id_store),
                "owner_name": user.name,
                "email": user.email,
                "location": {
                    "city": "Guadalajara, Jalisco",
                    "lat": 20.6596,
                    "lng": -103.3496
                }
            }
        }
        with open(self.archivo_config, "w") as f:
            json.dump(config_data, f, indent=4)
        return True

    #Datos para que el Rogi los muestre en el perfil del usuario
    #Transforma los datos crudos del JSON en un objeto tipo ConfigStats
    def get_app_stats(self) -> ConfigStats:
        """
        Transforma los datos crudos del disco duro en un Objeto Python.
        Rogi usa esto para rellenar los datos del usuario en la barra lateral o perfil.
        """
        #Si no hay registro, no hay perfil que mostrar
        if self.is_first_start():
            return None
        with open(self.archivo_config, "r") as f:
            config = json.load(f)
            perfil = config.get("store_profile", {})

            #Mapeamos el Diccionario a nuestro Modelo de Datos
            return ConfigStats(
                user_name=perfil.get("owner_name", "Usuario"),
                email=perfil.get("email", ""),
                theme_mode=True,
                current_date=date.today()
            )