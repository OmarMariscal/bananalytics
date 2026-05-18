"""
Motor de Aprendizaje Incremental — BanAnalytics Worker ML.

Implementa la Tarea 3 de la arquitectura:
  · Carga o crea modelos SGDRegressor desde models_database.
  · Aplica partial_fit() para actualización incremental (RF-04).
  · Serializa el modelo actualizado a bytes (pickle) y lo persiste en PostgreSQL.
  · Calcula RMSE para monitoreo de calidad del modelo y como margen de error
    interpretable en unidades del producto (expuesto en prediction_database).

Decisiones de diseño:
  - SGDRegressor con loss="squared_error" es equivalente a Ridge Regression online,
    ideal para series de tiempo con features continuos y cíclicos.
  - partial_fit() actualiza los pesos sin descartar lo aprendido → true online learning.
  - Cold Start: múltiples épocas con shuffle aleatorio para compensar que el modelo
    nunca ha visto estos datos y necesita más pasadas para converger.
  - RMSE en lugar de MSE: al estar en las mismas unidades que la variable objetivo
    (unidades de producto), puede usarse directamente como margin_of_error sin
    transformación adicional en los módulos consumidores.
  - load_or_create_model retorna el RMSE almacenado como tercer elemento de la
    tupla para que inference.py pueda leerlo sin un segundo viaje a la BD.
  - Los pesos del modelo son ~5 KB en pickle; almacenar en BYTEA de PostgreSQL
    es la decisión correcta para este volumen (300 productos).
"""
from __future__ import annotations

import io
import pickle
from datetime import datetime, timezone

import numpy as np
from sklearn.linear_model import SGDRegressor
from sklearn.metrics import mean_squared_error

from config.settings import get_settings
from db.connection import get_session
from db.models import ModeloML
from utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()

# ── Nombre canónico del tipo de modelo para almacenamiento ───────────────────
_MODEL_TYPE = "SGDRegressor-v2"

# ── Serialización ─────────────────────────────────────────────────────────────

def _serialize(model: SGDRegressor) -> bytes:
    """Convierte el modelo a bytes para almacenamiento en PostgreSQL BYTEA."""
    buf = io.BytesIO()
    pickle.dump(model, buf, protocol=pickle.HIGHEST_PROTOCOL)
    return buf.getvalue()


def _deserialize(data: bytes) -> SGDRegressor:
    """Reconstruye el modelo desde bytes de PostgreSQL BYTEA."""
    return pickle.loads(data)  # noqa: S301 — datos propios, origen confiable

# ── Construcción del Modelo ───────────────────────────────────────────────────

def _create_new_model() -> SGDRegressor:
    """
    Inicializa un SGDRegressor con hiperparámetros pensados para:
      · Datos de ventas con escala pequeña (~1-50 unidades/día).
      · Features normalizadas manualmente en pipeline.py (escala ~[−1, 1]).
      · Actualización incremental en ciclos de 24h.

    learning_rate="invscaling" con eta0=0.01 y power_t=0.25 decrece
    gradualmente para estabilizar el modelo con el tiempo.
    """
    return SGDRegressor(
        loss          = "squared_error",
        penalty       = "l2",
        alpha         = 0.0001,
        learning_rate = "invscaling",
        eta0          = 0.01,
        power_t       = 0.25,
        random_state  = 42,
    )

# ── Interfaz Pública ──────────────────────────────────────────────────────────

def load_or_create_model(barcode: str) -> tuple[SGDRegressor, bool, float]:
    """
    Recupera el modelo de models_database o crea uno nuevo.

    Retorna:
        (modelo, es_cold_start, rmse_almacenado)

        · es_cold_start = True  → no había modelo o tiene muy pocos ejemplos.
        · es_cold_start = False → modelo existente listo para partial_fit incremental.
        · rmse_almacenado       → RMSE guardado en el último entrenamiento, en unidades
                                  del producto. 0.0 si el modelo es nuevo (Cold Start).
                                  Inference.py lo consume directamente como margin_of_error
                                  sin necesidad de un segundo viaje a la BD.
    """
    with get_session() as session:
        register = (
            session.query(ModeloML)
            .filter_by(barcode=barcode)
            .first()
        )
        # Copiar todos los campos necesarios fuera de la sesión antes de cerrarla
        binary_data    = register.binary_model  if register else None
        total_examples = register.total_examples if register else 0
        stored_rmse    = register.last_rmse      if register else 0.0

    is_cold_start = (
        binary_data is None
        or (total_examples or 0) < _settings.min_examples_cold_start
    )

    if binary_data:
        try:
            model = _deserialize(binary_data)
            logger.debug(
                f"    📦 Modelo cargado · barcode={barcode} · "
                f"ejemplos={total_examples} · rmse={stored_rmse:.3f}"
            )
            return model, is_cold_start, float(stored_rmse or 0.0)
        except Exception as e:
            logger.warning(f"    ⚠️  Pickle corrupto para {barcode}, reiniciando: {e}")

    logger.info(f"    🌱 Cold Start · barcode={barcode} · ejemplos_previos={total_examples}")
    return _create_new_model(), True, 0.0

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
    for _ in range(n_epochs):
        idx = rng.permutation(len(X))
        model.partial_fit(X[idx], y[idx])

    return model


def calcule_rmse(
    model: SGDRegressor,
    X: np.ndarray,
    y: np.ndarray,
) -> float:
    """
    Calcula el RMSE (Root Mean Squared Error) del modelo sobre el set de entrenamiento.

    RMSE = √MSE: al expresarse en las mismas unidades que la variable objetivo
    (unidades de producto), puede usarse directamente como margen de error
    interpretable para el cliente final sin ninguna transformación adicional.

    Las predicciones negativas se recortan a 0 antes del cómputo (no se pueden
    vender −5 unidades) para que el error refleje el comportamiento real del sistema
    en producción, donde también se aplica max(0, pred).

    Retorna 0.0 si X está vacío (sin datos suficientes para calcular el error).
    """
    if len(X) == 0:
        return 0.0

    y_pred = np.clip(model.predict(X), 0, None)
    return float(np.sqrt(mean_squared_error(y, y_pred)))


def save_model(
    barcode: str,
    model: SGDRegressor,
    rmse: float,
    new_examples: int,
) -> None:
    """
    Persiste el modelo actualizado en models_database.
    Si ya existe un registro para ese barcode, lo actualiza (UPDATE).
    Si es nuevo, lo inserta (INSERT).

    Args:
        rmse: RMSE calculado tras el entrenamiento, en unidades del producto.
              Se almacena en last_rmse para ser consumido por inference.py
              como margin_of_error en cada predicción generada.
    """
    binary_data = _serialize(model)
    now         = datetime.now(timezone.utc)

    with get_session() as session:
        register = (
            session.query(ModeloML)
            .filter_by(barcode=barcode)
            .first()
        )

        if register:
            register.binary_model   = binary_data
            register.last_update    = now
            register.last_rmse      = rmse
            register.total_examples = (register.total_examples or 0) + new_examples
        else:
            session.add(ModeloML(
                barcode        = barcode,
                binary_model   = binary_data,
                last_update    = now,
                last_rmse      = rmse,
                total_examples = new_examples,
                type_model     = _MODEL_TYPE,
            ))

    logger.debug(
        f"    💾 Modelo guardado · barcode={barcode} · "
        f"RMSE={rmse:.4f} · +{new_examples} ejemplos"
    )
