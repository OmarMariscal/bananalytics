from pydantic import BaseModel
from typing import Literal
from datetime import date

class PredictionAlert(BaseModel):
    """Lo que el worker_ml genera y el frontend consume."""
    product_name: str
    barcode: str
    category: str
    image_url: str
    objective_date: date
    prediction: int           
    avg_weekly_sales: float
    percentage_average_deviation: float = 0.0
    type: Literal["superavit", "deficit", "none"]
    feature: bool | None = None