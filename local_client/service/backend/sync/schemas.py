from pydantic import BaseModel

from typing import List, Optional

class ProductSchema(BaseModel): #Representa la estructura del producto que pase por el escaner
    barcode: str
    amount: int

class TransaccionSchema(BaseModel): #Es la agrupacion por hora
    time: str
    products: List[ProductSchema]

class PaqueteVentasSchema(BaseModel): #Es el paquete final que se entrega a la nube
    id_store: int
    date: str
    day: int
    sales: List[TransaccionSchema]