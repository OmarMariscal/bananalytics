"""
Motor de Inferencia — BanAnalytics Worker ML.

Implementa las Tareas 4.1, 4.2 y 4.3 de la arquitectura:
  · Obtiene pronóstico de clima de Open-Meteo para los próximos N días.
  · Predice ventas por (tienda, producto, día).
  · Clasifica cada predicción como DÉFICIT / SUPERÁVIT / NONE (RF-05).
  · Limpia las predicciones viejas e inserta las nuevas en prediction_database.

─── Fórmulas implementadas ──────────────────────────────────────────────────

RF-05 (Variación porcentual):
    Variación = ((P - V_p) / V_p) * 100

    donde:
      P   = predicción del modelo (Integer ≥ 0)
      V_p = promedio diario de ventas del último mes (Float)

─── Manejo de ZeroDivisionError (RF-05 explícito) ───────────────────────────
    Si V_p = 0 y P > 0 → SUPERÁVIT atípico, feature=True.
    Si V_p = 0 y P = 0 → NONE, feature=False.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import openmeteo_requests
import pandas as pd
import requests_cache
from retry_requests import retry

from config.settings import get_settings
from db.connection import get_session
from db.models import Prediccion, Producto, TipoAlerta
from etl.pipeline import (
    build_features_inference,
    get_historical_average,
    wmo_to_weather_code,
)
from ml.training import load_or_create_model
from utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()


#  Cliente Open-Meteo 

def _build_openmeteo_client() -> openmeteo_requests.Client:
    cached_session = requests_cache.CachedSession(".cache_openmeteo", expire_after=3_600)
    retry_session  = retry(cached_session, retries=3, backoff_factor=0.5)
    return openmeteo_requests.Client(session=retry_session)


_openmeteo_client = _build_openmeteo_client()


#  Obtención de forecast 

def get_climate_forecast(lat: float, lon: float) -> list[dict]:
    """
    Solicita el pronóstico de los próximos N días a Open-Meteo.
    Retorna: [{"date": date, "temperatura": float, "weather_code": int}, ...]
    En caso de fallo de la API, devuelve forecast neutro para no detener el pipeline.
    """
    params = {
        "latitude":  lat,
        "longitude": lon,
        "daily": ["temperature_2m_max", "temperature_2m_min", "weather_code"],
        "timezone":      "America/Mexico_City",
        "forecast_days": _settings.prediction_days,
    }

    try:
        responses = _openmeteo_client.weather_api(_settings.open_meteo_url, params=params)
        response  = responses[0]
        daily     = response.Daily()

        temp_max  = daily.Variables(0).ValuesAsNumpy()
        temp_min  = daily.Variables(1).ValuesAsNumpy()
        wmo_codes = daily.Variables(2).ValuesAsNumpy().astype(int)
        temperatures = (temp_max + temp_min) / 2.0

        start_ts = pd.Timestamp(daily.Time(), unit="s", tz="America/Mexico_City")
        dates   = pd.date_range(start=start_ts, periods=_settings.prediction_days, freq="D")

        forecast = [
            {
                "date":         dates[i].date(),
                "temperatura":  float(temperatures[i]),
                "weather_code": wmo_to_weather_code(int(wmo_codes[i])),
            }
            for i in range(_settings.prediction_days)
        ]
        logger.debug(f"  🌤  Forecast obtenido para ({lat:.4f}, {lon:.4f})")
        return forecast

    except Exception as e:
        logger.error(f"  ❌ Open-Meteo no respondió para ({lat}, {lon}): {e}. Usando forecast por defecto.")
        return [
            {"date": date.today() + timedelta(days=i), "temperatura": 22.0, "weather_code": 1}
            for i in range(_settings.prediction_days)
        ]


#  Clasificación RF-05 

def _classify(
    prediction: int,
    historical_average: float,
) -> tuple[bool, TipoAlerta, float]:
    """
    Aplica la fórmula RF-05 y retorna (es_destacado, tipo, variacion_pct).

    Manejo explícito de ZeroDivisionError según el ERS:
      V_p = 0 y P > 0 → SUPERÁVIT atípico, feature=True.
      V_p = 0 y P = 0 → NONE, feature=False.
    """
    if historical_average <= 0:
        if prediction > 0:
            return True, TipoAlerta.superavit, float("inf")
        return False, TipoAlerta.none, 0.0

    variation = ((prediction - historical_average) / historical_average) * 100.0

    if variation <= _settings.deficit_threshould:
        return True, TipoAlerta.deficit, variation
    if variation >= _settings.superavit_threshould:
        return True, TipoAlerta.superavit, variation

    return False, TipoAlerta.none, variation


# Generación de predicciones por tienda 

def get_store_predictions(
    store_id: int,
    lat: float,
    lon: float,
    barcodes: list[str],
) -> int:
    """
    Genera y persiste predicciones de los próximos N días para todos los productos
    de una tienda, usando el clima local vía Open-Meteo.
    Retorna el número total de predicciones insertadas.
    """
    forecast = get_climate_forecast(lat, lon)

    with get_session() as session:
        productos_lista = session.query(Producto).filter(Producto.barcode.in_(barcodes)).all()
        productos_map: dict[str, dict] = {
            p.barcode: {"product_name": p.product_name, "category": p.category, "image_url": p.image_url}
            for p in productos_lista
        }

    inserted = 0

    for barcode in barcodes:
        info = productos_map.get(barcode)
        if not info:
            logger.warning(f"    ⚠️  Producto {barcode} no en product_database, omitido.")
            continue

        try:
            model, _ = load_or_create_model(barcode)
            average  = get_historical_average(barcode, store_id)
            news: list[Prediccion] = []

            for day in forecast:
                obj_date:    date  = day["date"]
                temperature:  float = day["temperatura"]
                weather_code: int   = day["weather_code"]

                future_X = build_features_inference(
                    fecha=obj_date, temperature=temperature,
                    weather_code=weather_code, store_id=store_id,
                )

                pred_raw = float(model.predict(future_X)[0])
                pred     = round(max(0, pred_raw))   # int ✅

                is_outstanding, type_, porcentual_desviation = _classify(pred, average)

                news.append(Prediccion(
                    store_id=store_id,
                    barcode=barcode,
                    product_name=info["product_name"],
                    category=info["category"],
                    image_url=info["image_url"],
                    objective_date=obj_date,
                    prediction=pred,                                         # Integer ✅
                    feature=is_outstanding,
                    type=type_,
                    percentage_average_deviation=porcentual_desviation,      # Float ✅
                ))

            # DELETE + INSERT atómico
            with get_session() as session:
                session.query(Prediccion).filter_by(
                    store_id=store_id, barcode=barcode
                ).delete(synchronize_session=False)
                session.bulk_save_objects(news)

            inserted += len(news)

        except Exception as e:
            logger.error(f"    ❌ Error predicciones tienda={store_id} barcode={barcode}: {e}")
            continue

    logger.info(f"  🏪 Tienda {store_id}: {inserted} predicciones · {len(barcodes)} productos")
    return inserted