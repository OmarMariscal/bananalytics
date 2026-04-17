"""
Pipeline ETL del Worker ML — BanAnalytics.

Responsabilidades:
  1. Extracción: consultas SQL seguras para obtener ventas históricas o recientes.
  2. Agregación diaria: transacciones individuales → totales diarios por (store, barcode).
  3. Feature Engineering: transformar fechas y clima en vectores numéricos
     que el SGDRegressor pueda comprender.

─── Ingeniería de Características ───────────────────────────────────────────
  Las 10 features en orden FIJO (debe ser idéntico en entrenamiento e inferencia):

  Índice │ Feature            │ Razón
  ───────┼────────────────────┼──────────────────────────────────────────────
     0   │ sin_dia_semana     │ Codificación cíclica: el modelo aprende que
     1   │ cos_dia_semana     │ domingo y lunes son "cercanos", no 6 vs 0.
     2   │ sin_dia_mes        │ Ídem para el día del mes (ciclo quincena).
     3   │ cos_dia_mes        │
     4   │ sin_mes            │ Estacionalidad anual.
     5   │ cos_mes            │
     6   │ es_quincena        │ 1 si estamos cerca del 15 o fin de mes (+40 % ventas).
     7   │ temperatura        │ Valor directo en °C.
     8   │ weather_code       │ Entero 0-5 (mapeado desde WMO via wmo_to_weather_code).
     9   │ store_id           │ El modelo global aprende diferencias entre tiendas.

─── Flujo del campo de clima ─────────────────────────────────────────────────
  BD (weather_resume_wmo_code: Integer WMO)
    → wmo_to_weather_code(wmo)          ← único punto de conversión
    → weather_code interno (0-5)        ← lo que ve el modelo
  Open-Meteo forecast (WMO int)
    → wmo_to_weather_code(wmo)          ← misma función, misma escala
    → weather_code interno (0-5)
"""

from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from sqlalchemy import text

from config.settings import get_settings
from db.connection import get_session
from utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()

# Constantes

N_FEATURES = 10

_DEFAULT_WEATHER_CODE = 1 # Parcialmente nublado: promedio razonable

# Mapeo de WMO codes de Open-Meteo a código interno acotado (0-5).
# Mismo mapeo para datos históricos (BD) y forecast (Open-Meteo).
# https://open-meteo.com/en/docs#weathervariables
_WMO_RANGES: list[tuple[set, int]] = [
    ({0}, 0),                       # Cielo despejado
    ({1, 2}, 1),                    # Principalmente despejado / parcialmente nublado
    ({3}, 2),                       # Cubierto
    (set(range(51, 68)), 3),        # Llovizna y lluvia ligera
    (set(range(80, 83)), 4),        # Chubascos moderados
    (set(range(95, 100)), 5),       # Tormenta eléctrica
]

#Conversión de clima

def wmo_to_weather_code(wmo: int) -> int:
    """
    Convierte cualquier código WMO de Open-Meteo a nuestro código interno (0-5).
    Aplica tanto a datos históricos de la BD como al forecast futuro.
    """
    for rango, code in _WMO_RANGES:
        if wmo in rango:
            return code
    return _DEFAULT_WEATHER_CODE

# Helpers de feature engineering

def _cyclic(value: float, max_value: float) -> tuple[float, float]:
    """Codificación cíclica seno/coseno para variables periódicas."""
    angle = 2 * math.pi * value / max_value
    return math.sin(angle), math.cos(angle)

def _is_fortnight(day: int) -> int:
    """Devuelve 1 si el día está cerca del 15 o del fin de mes."""
    return 1 if day in range(13, 18) or day >= 27 else 0

def _build_feature_vector(
    fecha: date,
    temperature: float,
    weather_code: int,
    store_id: int,
) -> np.array:
    """
    Construye el vector de N_FEATURES features para una observación.
    Este es el único lugar donde se define el orden de features;
    cualquier cambio aquí invalida todos los modelos existentes.
    """
    sin_day, cos_day = _cyclic(fecha.weekday(), 7)
    sin_day_month, cos_day_month = _cyclic(fecha.day, 31)
    sin_month, cos_month = _cyclic(fecha.month, 12)
    fortnight = _is_fortnight(fecha.day)
    
    return np.array(
        [
            sin_day, cos_day,
            sin_day_month, cos_day_month,
            sin_month, cos_month,
            fortnight,
            float(temperature),
            float(weather_code),
            float(store_id)
        ],
        dtype=np.float64,
    )
    
def _df_to_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """
    Convierte un DataFrame agregado diario a matrices (X, y) para sklearn.
    El DataFrame debe tener: date, store_id, amount, temperature, weather_code.
    """
    if df.empty:
        return np.empty((0, N_FEATURES)), np.empty(0)

    rows_X = []
    for _, row in df.iterrows():
        vec = _build_feature_vector(
            fecha = row["date"],
            temperature=float(row.get("temperature") or 20.0),
            weather_code=int(row.get("weather_code") or _DEFAULT_WEATHER_CODE),
            store_id=int(row["store_id"]),
        )
        rows_X.append(vec)
        
    X = np.vstack(rows_X)
    y = df["amount"].values.astype(np.float64)
    return X, y

def _aggregate_raw_sales(rows: list, columns: list[str]) -> pd.DataFrame:
    """
    Agrega filas crudas de sales_database a totales diarios por (store, barcode, date).

    weather_resume_wmo_code (Integer WMO) → wmo_to_weather_code() → código interno.
    Maneja NULLs con valores por defecto seguros.
    """
    if not rows:
        return pd.DataFrame()
    
    df = pd.DataFrame(rows, columns=columns)
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["temperature"] = pd.to_numeric(df["temperature"], errors="coerce")

    # Conversión WMO → código interno. NULLs reciben _DEFAULT_WEATHER_CODE.
    df["weather_code"] = df["weather_resume_wmo_code"].apply(
        lambda wmo: wmo_to_weather_code(int(wmo)) if wmo is not None else _DEFAULT_WEATHER_CODE
    )

    daily = (
        df.groupby(["store_id", "barcode", "date"])
        .agg(
            amount=("amount", "sum"),
            temperature=("temperature", "mean"),
            weather_code=("weather_code", lambda s: int(s.mode().iloc[0]) if not s.dropna().empty else _DEFAULT_WEATHER_CODE),
        )
        .reset_index()
    )

    global_temp_mean = daily["temperature"].mean()
    daily["temperature"] = daily["temperature"].fillna(
        global_temp_mean if not math.isnan(global_temp_mean) else 22.0
    )

    return daily

# Funciones de Extracción
def extract_historic_sales(barcode: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Extrae TODO el historial de ventas para un barcode (modo Cold Start).
    """
    query = text("""
        SELECT store_id, barcode, date, amount, temperature, weather_resume_wmo_code
        FROM sales_database
        WHERE barcode = :barcode
        ORDER BY date ASC, store_id ASC
    """)
    
    with get_session() as session:
        result = session.execute(query, {"barcode": barcode})
        rows = result.fetchall()
    
    if not rows:
        logger.debug(f"  Sin historial para barcode={barcode}")
        return np.empty((0, N_FEATURES)), np.empty(0)
    
    cols = ["store_id", "barcode", "date", "amount", "temperature", "weather_resume_wmo_code"]
    daily = _aggregate_raw_sales(rows, cols)
    return _df_to_matrix(daily)

def extract_recently_sales(
    barcode: str,
    days: Optional[int] = None,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Extrae ventas de los últimos N días para entrenamiento incremental.
    """
    days = days or _settings.training_window_days
    cut_off_date = date.today() - timedelta(days=days)
    
    query = text("""
        SELECT store_id, barcode, date, amount, temperature, weather_resume_wmo_code
        FROM sales_database
        WHERE barcode = :barcode
          AND date >= :cut_off_date
        ORDER BY date ASC, store_id ASC
    """)
    
    with get_session() as session:
        result = session.execute(query, {"barcode": barcode, "cut_off_date": cut_off_date})
        rows = result.fetchall()
        
    if not rows:
        return np.empty((0, N_FEATURES)), np.empty(0)
    
    cols = ["store_id", "barcode", "date", "amount", "temperature", "weather_resume_wmo_code"]
    daily = _aggregate_raw_sales(rows, cols)
    return _df_to_matrix(daily)

def build_features_inference(
    fecha: date,
    temperature: float,
    weather_code: int,
    store_id: int,
) -> np.ndarray:
    """
    Construye el vector de features para una fecha FUTURA (inferencia).
    Retorna shape (1, N_FEATURES) listo para model.predict().
    weather_code ya debe ser el código interno (0-5), no el WMO raw.
    """
    vec = _build_feature_vector(
        fecha=fecha,
        temperature=temperature,
        weather_code=weather_code,
        store_id=store_id,
    )
    return vec.reshape(1, -1) 

# Funciones de Consulta
def get_historical_average(barcode: str, store_id: int) -> float:
    """
    Calcula el promedio diario de ventas del último mes para una tienda y producto.
    Retorna 0.0 si no hay datos (el llamador maneja el caso ZeroDivision).
    """
    cut_off_date = date.today() - timedelta(days=30)

    query = text("""
        SELECT COALESCE(AVG(daily_total), 0.0)
        FROM (
            SELECT date, SUM(amount) AS daily_total
            FROM sales_database
            WHERE barcode   = :barcode
              AND store_id  = :store_id
              AND date      >= :cut_off_date
            GROUP BY date
        ) sub
    """)

    with get_session() as session:
        result = session.execute(
            query,
            {"barcode": barcode, "store_id": store_id, "cut_off_date": cut_off_date},
        )
        average = result.scalar()

    return float(average or 0.0)


def count_barcode_examples(barcode: str) -> int:
    """Cuenta registros brutos de venta para detectar Cold Start."""
    query = text("SELECT COUNT(*) FROM sales_database WHERE barcode = :barcode")
    with get_session() as session:
        result = session.execute(query, {"barcode": barcode})
        return int(result.scalar() or 0)


def get_all_barcodes() -> list[str]:
    """Retorna todos los barcodes con al menos una venta registrada."""
    query = text("SELECT DISTINCT barcode FROM sales_database ORDER BY barcode")
    with get_session() as session:
        result = session.execute(query)
        return [row[0] for row in result.fetchall()]


def get_all_stores() -> list[dict]:
    """Retorna todas las tiendas con sus coordenadas para el forecast de clima."""
    query = text(
        "SELECT store_id, latitude, longitude FROM stores_database ORDER BY store_id"
    )
    with get_session() as session:
        result = session.execute(query)
        return [
            {"store_id": row[0], "latitude": row[1], "longitude": row[2]}
            for row in result.fetchall()
        ]