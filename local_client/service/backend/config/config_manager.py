#LEER Y ESCRIBIR EL ARCHIVO SETTINGS.JSON

import os
import json
from datetime import date
from shared.models.user import User
from shared.models.info_config import ConfigStats


class ConfigManager:
    #Definir el nombre del archivo
    def __init__(self):
        self.archivo_config = "settings.json"

    #Validar si es el primer inicio al buscar el ARCHIVO_CONFIG
    def is_first_start(self) -> bool:
        if not os.path.exists(self.archivo_config):
            return True #Si no existe,el usuario nunca se ha registrado, por lo tanto devuelve True
        try:
            with open(self.archivo_config, "r") as f:
                config = json.load(f)
                return not config.get("system", {}).get("first_launch_completed", False) #Si existe el archivo creado, pero el valor es False, es primer inicio
        except (json.JSONDecodeError, KeyError):
            return True

def create_configurations(self, user: User, id_store: str) -> bool:
    #Organiza los datos como los tenemos definidos
    config_data = {
        #Rutas tecnicas
        "system": {
            "first_launch_completed": True,
            "local_db_path": "./tienda.db"
        },
        #Datos del dueno
        "store_profile": {
            "id_store": int(id_store),
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
    if self.is_first_start():
        return None
    with open(self.archivo_config, "r") as f:
        config = json.load(f)
        perfil = config.get("store_profile", {})
        return ConfigStats(
            user_name=perfil.get("owner_name", "Usuario"),
            email=perfil.get("email", ""),
            theme_mode=True,
            curent_date=date.today()
        )