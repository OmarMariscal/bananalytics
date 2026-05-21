"""
Motor de Inferencia — BanAnalytics Worker ML.

Implementa las Tareas 4.1, 4.2 y 4.3 de la arquitectura:
  · Obtiene pronóstico de clima de Open-Meteo para los próximos N días.
  · Predice ventas diarias internas y las agrega a un total semanal.
  · Clasifica cada predicción semanal como DÉFICIT / SUPERÁVIT / NONE (RF-05).
  · Limpia las predicciones viejas e inserta las nuevas en prediction_database.

─── Modelo de predicción ─────────────

  El worker genera UN registro por (tienda, producto) con:

    objective_date  = hoy + prediction_days
      Fecha horizonte de la ventana de predicción. Informa al cliente hasta
      qué día aplica el pronóstico.

    prediction      = Σ predicciones_diarias[día 1..N]
      Total de unidades esperadas a vender durante la semana completa.
      Cada día se predice internamente con su propio vector de features
      (clima, día de semana, quincena…) y se suman al final.

    avg_weekly_sales = promedio_diario × prediction_days
      Volumen habitual de referencia del último mes para esta (tienda, producto).
      Base de la clasificación RF-05 y contexto para el cliente.

    margin_of_error = round(√N × RMSE_modelo)
      Margen de error semanal derivado del RMSE diario del modelo.
      Estadísticamente preciso para errores independientes entre días:
        RMSE_semanal = √(Σ RMSE_día²) = √(N × RMSE²) = √N × RMSE
      Interpretación para el cliente:
        ventas_reales ∈ [prediction − margin_of_error, prediction + margin_of_error]

─── Fórmula RF-05 (Variación porcentual) ──────────────

    Variación = ((prediction − avg_weekly_sales) / avg_weekly_sales) × 100

    La comparación es semanal vs semanal, por lo que los umbrales configurados
    en settings (deficit_threshould, superavit_threshould) aplican sin ajuste.

─── Manejo de ZeroDivisionError (RF-05 explícito) ─────
    Si avg_weekly = 0 y prediction > 0 → SUPERÁVIT atípico, feature=True.
    Si avg_weekly = 0 y prediction = 0 → NONE, feature=False.
"""

from __future__ import annotations

import math
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

#  Constantes 

# Cap de seguridad por día antes de agregar al total semanal.
# Evita que un día con predicción desbocada infle el total semanal.
_MAX_DAILY_PRED = 9_999

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
        "latitude":      lat,
        "longitude":     lon,
        "daily":         ["temperature_2m_max", "temperature_2m_min", "weather_code"],
        "timezone":      "America/Mexico_City",
        "forecast_days": _settings.prediction_days,
    }

    try:
        responses    = _openmeteo_client.weather_api(_settings.open_meteo_url, params=params)
        response     = responses[0]
        daily        = response.Daily()

        temp_max     = daily.Variables(0).ValuesAsNumpy()
        temp_min     = daily.Variables(1).ValuesAsNumpy()
        wmo_codes    = daily.Variables(2).ValuesAsNumpy().astype(int)
        temperatures = (temp_max + temp_min) / 2.0

        start_ts = pd.Timestamp(daily.Time(), unit="s", tz="America/Mexico_City")
        dates    = pd.date_range(start=start_ts, periods=_settings.prediction_days, freq="D")

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
        logger.error(
            f"  ❌ Open-Meteo no respondió para ({lat}, {lon}): {e}. "
            f"Usando forecast por defecto."
        )
        return [
            {
                "date":         date.today() + timedelta(days=i),
                "temperatura":  22.0,
                "weather_code": 1,
            }
            for i in range(_settings.prediction_days)
        ]

#  Clasificación RF-05 

def _classify(
    prediction: int,
    weekly_average: float,
) -> tuple[bool, TipoAlerta, float]:
    """
    Aplica la fórmula RF-05 comparando predicción semanal vs promedio semanal.

    La escala semanal vs semanal garantiza que los umbrales configurados en
    settings (deficit_threshould, superavit_threshould) apliquen sin ajuste.

    Retorna: (es_destacado, tipo_alerta, variacion_porcentual)

    Manejo explícito de ZeroDivisionError según el ERS:
      avg_weekly = 0 y prediction > 0 → SUPERÁVIT atípico, feature=True.
      avg_weekly = 0 y prediction = 0 → NONE, feature=False.
    """
    if weekly_average <= 0:
        if prediction > 0:
            return True, TipoAlerta.superavit, float("inf")
        return False, TipoAlerta.none, 0.0

    variation = ((prediction - weekly_average) / weekly_average) * 100.0

    if variation <= _settings.deficit_threshould:
        return True, TipoAlerta.deficit, variation
    if variation >= _settings.superavit_threshould:
        return True, TipoAlerta.superavit, variation

    return False, TipoAlerta.none, variation

#  Agregación semanal 

def _aggregate_weekly_prediction(
    model,
    forecast: list[dict],
    store_id: int,
    barcode: str,
) -> int:
    """
    Predice las ventas de cada día del forecast y devuelve el total semanal.

    Cada día se predice de forma independiente con su propio vector de features
    (clima, día de semana, quincena…), aplicando el cap diario de seguridad.
    El total es la suma de los N valores diarios.

    Args:
        model:    SGDRegressor ya entrenado para este barcode.
        forecast: Lista de dicts con date, temperatura y weather_code por día.
        store_id: ID de la tienda — incluido en el vector de features.
        barcode:  Solo para logging en caso de predicción fuera de rango.

    Returns:
        Total de unidades predichas para la semana (entero ≥ 0).
    """
    weekly_total = 0

    for day in forecast:
        future_X = build_features_inference(
            fecha        = day["date"],
            temperature  = day["temperatura"],
            weather_code = day["weather_code"],
            store_id     = store_id,
        )

        pred_raw = float(model.predict(future_X)[0])
        pred_day = int(round(max(0, min(pred_raw, _MAX_DAILY_PRED))))

        if pred_raw > _MAX_DAILY_PRED:
            logger.warning(
                f"    ⚠️  Predicción diaria fuera de rango ({pred_raw:.0f}) · "
                f"barcode={barcode} store={store_id} fecha={day['date']} "
                f"— recortada a {pred_day}"
            )

        weekly_total += pred_day

    return weekly_total

# Generación de predicciones por tienda

def get_store_predictions(
    store_id: int,
    lat: float,
    lon: float,
    barcodes: list[str],
) -> int:
    """
    Genera y persiste UNA predicción semanal por producto para una tienda.

    Flujo por cada barcode:
      1. Carga el modelo y su RMSE desde models_database (sin consulta extra a BD).
      2. Calcula el promedio semanal de ventas del último mes.
      3. Predice las ventas de cada día del forecast y las suma → total semanal.
      4. Calcula margin_of_error = round(√N × RMSE).
      5. Clasifica el total semanal contra el promedio semanal (RF-05).
      6. DELETE + INSERT atómico del registro de esa (tienda, producto).

    Args:
        store_id: ID de la tienda.
        lat, lon: Coordenadas para el forecast de Open-Meteo.
        barcodes: Lista de barcodes a procesar.

    Returns:
        Número de predicciones insertadas (una por barcode exitoso).
    """
    forecast       = get_climate_forecast(lat, lon)
    objective_date = date.today() + timedelta(days=_settings.prediction_days)

    with get_session() as session:
        productos_lista = session.query(Producto).filter(Producto.barcode.in_(barcodes)).all()
        productos_map: dict[str, dict] = {
            p.barcode: {
                "product_name": p.product_name,
                "category":     p.category,
                "image_url":    p.image_url,
            }
            for p in productos_lista
        }

    inserted = 0

    for barcode in barcodes:
        info = productos_map.get(barcode)
        if not info:
            logger.warning(f"    ⚠️  Producto {barcode} no en product_database, omitido.")
            continue

        try:
            #  Modelo y margen de error semanal — sin consulta extra a la BD 
            model, _, model_rmse = load_or_create_model(barcode)

            if not hasattr(model, "coef_"):
                logger.warning(
                    f"    ⚠️  Modelo de {barcode} sin entrenamiento previo — "
                    f"omitido hasta el próximo ciclo."
                )
                continue
            
            margin               = int(round(math.sqrt(_settings.prediction_days) * model_rmse))

            #  Referencia histórica semanal 
            daily_avg  = get_historical_average(barcode, store_id)
            avg_weekly = int(round(daily_avg * _settings.prediction_days, 2))

            #  Predicción agregada de la semana 
            weekly_pred = _aggregate_weekly_prediction(model, forecast, store_id, barcode)

            #  Clasificación RF-05 (semanal vs semanal) 
            is_outstanding, type_, pct_deviation = _classify(weekly_pred, avg_weekly)

            #  DELETE + INSERT atómico 
            with get_session() as session:
                session.query(Prediccion).filter_by(
                    store_id=store_id, barcode=barcode
                ).delete(synchronize_session=False)

                session.add(Prediccion(
                    store_id                     = store_id,
                    barcode                      = barcode,
                    product_name                 = info["product_name"],
                    category                     = info["category"],
                    image_url                    = info["image_url"],
                    objective_date               = objective_date,
                    prediction                   = weekly_pred,
                    feature                      = is_outstanding,
                    type                         = type_,
                    percentage_average_deviation = pct_deviation,
                    avg_weekly_sales             = avg_weekly,
                    margin_of_error              = margin,
                ))

            inserted += 1

        except Exception as e:
            logger.error(
                f"    ❌ Error predicciones tienda={store_id} barcode={barcode}: {e}"
            )
            continue

    logger.info(f"  🏪 Tienda {store_id}: {inserted} predicciones · {len(barcodes)} productos")
    return inserted