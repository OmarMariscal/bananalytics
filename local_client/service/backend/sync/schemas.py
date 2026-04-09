from pydantic import BaseModel

from typing import List, Optional

class ProductSchema(BaseModel):
    barcode: str
    amount: int

class TransaccionSchema(BaseModel):
    time: str
    products: List[ProductSchema]

class PaqueteVentasSchema(BaseModel):
    id_store: int
    date: str
    day: int
    sales: List[TransaccionSchema]