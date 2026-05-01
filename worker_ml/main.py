"""
Orquestador del Worker ML — BanAnalytics.

Flujo de ejecución:
    1. Verificar conexión a BD (fail-fast).
    2. Asegurar existencia de tablas (idempotente).
    3. Obtener catálogo de barcodes y tiendas.
    4. FASE ENTRENAMIENTO: actualizar modelos (Cold Start o incremental).
    5. FASE INFERENCIA: generar predicciones por tienda para los próximos N días.

Manejo de fallos (RF-04): 3 intentos con 15 min de espera entre cada uno.
"""

import sys
import time
from datetime import datetime, timezone

from config.settings import get_settings
from db.connection import create_tables, check_connection
from etl.pipeline import(
    extract_historic_sales,
    extract_recently_sales,
    get_all_stores,
    get_all_barcodes,
)
from ml.training import(
    calcule_mse,
    load_or_create_model,
    incremental_train,
    save_model,
)
from ml.inference import get_store_predictions
from utils.logger import get_logger

logger = get_logger(__name__)
_settings = get_settings()

_MAX_TRYS = 3
_SECONDS_WAIT = 15 * 60

def _training_fase(barcodes: list[str]) -> None:
    total = len(barcodes)
    logger.info(f"🧠 Fase Entrenamiento — {total} productos")
    
    for i, barcode in enumerate(barcodes, 1):
        try:
            model, is_cold_start = load_or_create_model(barcode)
            
            if is_cold_start:
                X, y = extract_historic_sales(barcode)
                n_epochs = _settings.cold_start_epochs
            else:
                X, y = extract_recently_sales(barcode)
                n_epochs = 1
            
            if len(X) == 0:
                logger.warning(f"  [{i:>3}/{total}] ⚠️  Sin datos para {barcode} — omitido")
                continue
            
            model = incremental_train(model, X, y, n_epochs=n_epochs)
            mse = calcule_mse(model, X, y)
            save_model(barcode, model, mse, new_examples=len(X))
            
            mode = "Cold Start" if is_cold_start else "Incremental"
            logger.info(
                f"  [{i:>3}/{total}] ✅ {mode:<12} | "
                f"barcode={barcode} | n={len(X):>4} | MSE={mse:.3f}"
            )
        except Exception as e:
            logger.error(f"  [{i:>3}/{total}] ❌ Error en {barcode}: {e}")
            continue
    logger.info("✅ Fase Entrenamiento completada.")

def _inference_fase(barcodes: list[str], stores: list[dict]) -> None:
    logger.info(f"🔮 Fase Inferencia — {len(stores)} tiendas × {len(barcodes)} productos")
    total_predictions = 0
    
    for store in stores:
        try:
            n = get_store_predictions(
                store_id=store["store_id"],
                lat=store["latitude"],
                lon=store["longitude"],
                barcodes=barcodes,
            )
            total_predictions += n
        except Exception as e:
            logger.error(f"  ❌ Error total en tienda {store['store_id']}: {e}")
            continue

    logger.info(f"✅ Fase Inferencia completada. Total predicciones: {total_predictions:,}")

def _execute_worker() -> None:
    start = datetime.now(timezone.utc)
    separator = "═" * 62

    logger.info(separator)
    logger.info(f"  🚀  BanAnalytics Worker ML — {start.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    logger.info(f"  📅  Días de predicción : {_settings.prediction_days}")
    logger.info(f"  📉  Umbral DÉFICIT     : {_settings.deficit_threshould:.0f}%")
    logger.info(f"  📈  Umbral SUPERÁVIT   : {_settings.superavit_threshould:.0f}%")
    logger.info(separator)
    
    if not check_connection():
        logger.critical("❌ Sin conexión a Neon. Abortando.")
        sys.exit(1)
    
    create_tables()
    
    barcodes = get_all_barcodes()
    stores = get_all_stores()
    
    if not barcodes:
        logger.warning("⚠️  Sin productos en la BD. Recomendación: Para pruebas usa el data_forger.py")
        sys.exit(0)

    logger.info(f"📊 Catálogo: {len(barcodes)} productos | {len(stores)} tiendas")

    _training_fase(barcodes)
    _inference_fase(barcodes, stores)
    
    duration_min = (datetime.now(timezone.utc) - start).total_seconds() / 60
    logger.info(separator)
    logger.info(f"  🏁  Worker finalizado en {duration_min:.1f} min.")
    logger.info(separator)
    

def main() -> None:
    for attempt in range(1, _MAX_TRYS + 1):
        try:
            _execute_worker()
            sys.exit(0)
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"💥 Intento {attempt}/{_MAX_TRYS} falló: {e}")
            if attempt < _MAX_TRYS:
                logger.info(f"⏳ Reintentando en {_SECONDS_WAIT // 60} minutos...")
                time.sleep(_settings) 
            else:
                logger.critical("💀 Todos los intentos fallaron. Revisar logs y estado de Neon.")
                sys.exit(1)
                
if __name__ == "__main__":
    main() 
    