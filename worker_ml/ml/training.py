"""
Motor de Aprendizaje Incremental — BanAnalytics Worker ML.

Implementa la Tarea 3 de la arquitectura:
  · Carga o crea modelos SGDRegressor desde models_database.
  · Aplica partial_fit() para actualización incremental (RF-04).
  · Serializa el modelo actualizado a bytes (pickle) y lo persiste en PostgreSQL.
  · Calcula MSE para monitoreo de calidad del modelo.

Decisiones de diseño:
  - SGDRegressor con loss="squared_error" es equivalente a Ridge Regression online,
    ideal para series de tiempo con features continuos y cíclicos.
  - partial_fit() actualiza los pesos sin descartar lo aprendido → true online learning.
  - Cold Start: múltiples épocas con shuffle aleatorio para compensar que el modelo
    nunca ha visto estos datos y necesita más pasadas para converger.
  - Los pesos del modelo son ~5 KB en pickle; almacenar en BYTEA de PostgreSQL
    es la decisión correcta para este volumen (300 productos).
"""
from __future__ import annotations

import io
import pickle
from datetime import datetime, timezone
from typing import Optional

import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error

from config.settings import get_settings
from db.connection import get_session
from db.models import ModeloML
from utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()

#  Nombre canónico del tipo de modelo para almacenamiento
_MODEL_TYPE = "SGDRegressor-v1"

# Serialización
def _serialize(model: SGDRegressor) -> bytes:
    """Convierte el modelo a bytes para almacenamiento en PostgreSQL BYTEA."""
    buf = io.BytesIO()
    pickle.dump(model, buf, protocol=pickle.HIGHEST_PROTOCOL)
    return buf.getvalue()

def _deserialize(data: bytes) -> SGDRegressor:
    """Reconstruye el modelo desde bytes de PostgreSQL BYTEA."""
    return pickle.loads(data) # noqa: S301 — datos propios, origen confiable

# Construcción del Modelo

def _create_new_model() -> SGDRegressor:
    """
    Inicializa un SGDRegressor con hiperparámetros pensados para:
      · Datos de ventas con escala pequeña (~1-50 unidades/día).
      · Features normalizadas cíclicamente (sin/cos) más enteros.
      · Actualización incremental en ciclos de 24h.

    learning_rate="invscaling" con eta0=0.01 y power_t=0.25 decrece
    gradualmente para estabilizar el modelo con el tiempo.
    """
    return SGDRegressor(
        loss = "squared_error",
        penalty = "l2",
        alpha = 0.0001,
        learning_rate = "invscaling",
        eta0 = 0.01,
        power_t = 0.25,
        random_state = 42,
    )
    
# Interfaz Pública

def load_or_create_model(barcode: str) -> tuple[SGDRegressor, bool]:
    """
    Recupera el modelo de models_database o crea uno nuevo.

    Retorna:
        (modelo, es_cold_start)
        es_cold_start = True  → no había modelo o tiene muy pocos ejemplos.
        es_cold_start = False → modelo existente listo para partial_fit incremental.
    """
    with get_session() as session:
        register = (
            session.query(ModeloML)
            .filter_by(barcode=barcode)
            .first()
        )
        # Copiar datos fuera de la sesión antes de cerrarla
        binary_data = register.binary_model if register else None
        total_examples = register.total_examples if register else 0
        
    is_cold_start = (
        binary_data is None
        or (total_examples or 0) < _settings.min_examples_cold_start
    )
    
    if binary_data and not is_cold_start:
        try:
            model = _deserialize(binary_data)
            logger.debug(f"    📦 Modelo cargado · barcode={barcode} · ejemplos={total_examples}")
            return model, False
        except Exception as e:
            # Pickle corrupto: inicializar de nuevo en lugar de abortar.
            logger.warning(f"    ⚠️  Pickle corrupto para {barcode}, reiniciando: {e}")
            
    logger.info(f"    🌱 Cold Start · barcode={barcode} · ejemplos_previos={total_examples}")
    return _create_new_model(), True

def incremental_train(
    model: SGDRegressor,
    X: np.ndarray,
    y: np.ndarray,
    n_epochs: int = 1,
) -> SGDRegressor:
    """
    Aplica partial_fit() al modelo.

    Args:
        n_epochs: Número de pasadas sobre los datos.
                  Use > 1 en Cold Start para mejorar convergencia inicial.
                  Use 1 en modo incremental normal.
    """
    if len(X) == 0:
        logger.warning("    ⚠️  Sin datos de entrenamiento, se omite partial_fit.")
        return model
    
    rng = np.random.default_rng(seed=42)
    for epoch in range(n_epochs):
        idx = rng.permutation(len(X))
        model.partial_fit(X[idx], y[idx])
    
    return model


def calcule_mse(
    model: SGDRegressor,
    X: np.ndarray,
    y: np.ndarray,
) -> float:
    """
    Calcula MSE del modelo en el set de entrenamiento.
    Las predicciones negativas se recortan a 0 (no se pueden vender -5 unidades).
    """
    if len(X) == 0:
        return float("inf")
    
    y_pred = np.clip(model.predict(X), 0, None)
    return float(mean_squared_error(y, y_pred))


def save_model(
    barcode: str,
    model: SGDRegressor,
    mse: float,
    new_examples: int,
) -> None:
    """
    Persiste el modelo actualizado en models_database.
    Si ya existe un registro para ese barcode, lo actualiza (UPDATE).
    Si es nuevo, lo inserta (INSERT).
    """
    binary_data = _serialize(model)
    now = datetime.now(timezone.utc)
    
    with get_session() as session:
        register = (
            session.query(ModeloML)
            .filter_by(barcode=barcode)
            .first()
        )
        
        if register:
            register.binary_model = binary_data
            register.last_update = now
            register.last_mse = mse
            register.total_examples = (register.total_examples or 0) + new_examples
        else:
            new = ModeloML(
               barcode = barcode,
               binary_model = binary_data,
               last_update = now,
               last_mse = mse,
               total_examples = new_examples,
               type_model = _MODEL_TYPE 
            )
            session.add(new)
            

    logger.debug(
        f"    💾 Modelo guardado · barcode={barcode} · "
        f"MSE={mse:.4f} · +{new_examples} ejemplos"
    )