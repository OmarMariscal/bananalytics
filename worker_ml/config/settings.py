"""
Configuración central del Worker ML.

Usa Pydantic Settings para:
  - Validación de tipos en el arranque (falla rápido antes de hacer nada).
  - Lectura automática desde .env o variables de entorno de GitHub Actions.
  - Singleton cacheado con @lru_cache para no re-parsear en cada módulo.
"""

from functools import lru_cache

from pydantic import field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    #Base de Datos
    database_url: PostgresDsn
    
    #Horizonte de predicciones
    prediction_days: int = 7
    
    #Umbrales de clasificación RF-05 (en porcentaje)
    # Variación <= umbral_deficit -> DÉFICIT (ej: -15.0 = caída del 15%)
    # Variación >= umbral_superátiv -> SUPERÁVIT (ej: +15.0 = alza del 15%)
    deficit_threshould: float = -15.0
    superavit_threshould: float = 15.0
    
    # Parámetros de entrenamiento
    # Número mínimo de ejemplos acumulados antes de salir del modo Cold Start
    min_examples_cold_start: int = 30
    # Cuántos días hacía atrás extraeren el modo incremental.
    training_window_days: int = 2
    # Épocas de entrenamiento en Cold Start (múltiples pasadas compensan pocos datos)
    cold_start_epochs: int = 10
    
    #API del Clima
    open_meteo_url: str = "https://api.open-meteo.com/v1/forecast"
    
    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding= "utf-8",
        case_sensitive = False,
        extra = "ignore",
    )
    
    # Validaciones de negocio
    
    @field_validator("deficit_threshould")
    @classmethod
    def deficit_must_be_negative(cls, v: float) -> float:
        if v >= 0:
            raise ValueError(
                f"deficit_threshould debe ser negativo (ej: -15.0). Recibido: {v}"
            )
        return v

    @field_validator("superavit_threshould")
    @classmethod
    def superavit_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(
                f"superavit_threshould debe ser positivo (ej: 15.0). Recibido {v}"
            )
        return v
    
    @field_validator("prediction_days")
    @classmethod
    def valid_days(cls, v: int) -> int:
        if not 1 <= v <= 16:
            raise ValueError(
                f"prediction_days debe estar entre 1 y 16 (Límite de Open-Meteo)."
            )
        return v

@lru_cache
def get_settings() -> Settings:
    """
    Singleton de configuración.
    Falla en el arranque si falta DATABASE_URL o algún valor es inválido.
    """
    return Settings()