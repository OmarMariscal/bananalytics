"""
Modelos de Validación de Datos.
Actúan como el "escudo" de la aplicación. Validan que los datos empaquetados
tengan la estructura perfecta antes de enviarlos a la API para no contaminar
los modelos de Machine Learning.
"""

from pydantic import BaseModel, field_validator
from typing import List

class ProductSchema(BaseModel):
    """Representa un producto individual dentro de una transacción."""
    barcode: str
    amount: int

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        """Bloquea cantidades negativas o ceros que arruinarían el modelo predictivo."""
        if v <= 0:
            raise ValueError("amount debe ser mayor a 0")
        return v

class TransaccionSchema(BaseModel):
    """Agrupación de productos vendidos dentro de un bloque temporal."""
    time: str
    products: List[ProductSchema]

    @field_validator("time")
    @classmethod
    def time_format_valido(cls, v):
        """Asegura que el SyncDaemon no genere horas malformadas (ej. 25:00:00)."""
        try:
            datetime_obj = __import__("datetime")
            datetime_obj.datetime.strptime(v, "%H:%M:%S")
        except ValueError:
            raise ValueError(f"El campo 'time' debe tener formato HH:MM:SS, recibido: '{v}'")
        return v

class PaqueteVentasSchema(BaseModel):
    """Payload final que se entrega a la nube para sincronizar."""
    id_store: int
    date: str
    day: int
    sales: List[TransaccionSchema]

    @field_validator("day")
    @classmethod
    def day_en_rango(cls, v):
        """Asegura que el día de la semana sea congruente (1 = Lunes, 7 = Domingo)."""
        if not 1 <= v <= 7:
            raise ValueError(f"'day' debe estar entre 1 y 7, recibido: {v}")
        return v