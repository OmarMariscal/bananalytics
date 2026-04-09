from pydantic import BaseModel
from datetime import date

class ConfigStats(BaseModel):
    """Lo que el worker_ml genera y el frontend consume."""
    user_name: str
    email: str
    theme_mode: bool
    current_date: date