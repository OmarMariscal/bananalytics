"""
Data Forge — Generador de Datos Sintéticos · BanAnalytics.

USO EXCLUSIVO DE DESARROLLO. Nunca ejecutar en producción.

Genera un historial de ventas matemáticamente coherente inyectando:
  · Tendencias de clima por ciudad y mes (basadas en México real).
  · Efecto de día de semana (+30 % fines de semana).
  · Efecto quincena (+40 % cerca del día 15 y fin de mes).
  · Sensibilidad de categoría a la temperatura (bebidas frías vs abarrotes).
  · Ruido de Poisson (distribución realista para conteo de ventas).

Ejecutar desde la raíz del proyecto:
    python -m scripts.data_forge
    python -m scripts.data_forge --months 6
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from db.connection import create_tables, get_session
from db.models import Producto, Tienda, Venta
from utils.logger import get_logger

logger = get_logger("data_forge")

random.seed(42)
np.random.seed(42)

STORES: list[dict] = [
    {"owner_name": "José Madero",   "email": "jose@abarrotesgdl.com", "city": "Guadalajara",      "latitude": 20.6534, "longitude": -103.3440},
    {"owner_name": "Laura Pergolizzi",      "email": "lp@tiendacdmx.com",    "city": "Ciudad de México",  "latitude": 19.4326, "longitude": -99.1332},
    {"owner_name": "Till Lindelman",  "email": "rammst@miscelamty.com",  "city": "Monterrey",         "latitude": 25.6866, "longitude": -100.3161},
    {"owner_name": "Ana Flores",       "email": "ana@abarrotespue.com",    "city": "Puebla",            "latitude": 19.0414, "longitude": -98.2063},
    {"owner_name": "Jorge Ramírez",    "email": "jorge@tiendacun.com",     "city": "Cancún",            "latitude": 21.1619, "longitude": -86.8515},
]

PRODUCTS: list[tuple[str, str, str, str]] = [
    ("7501055305255", "Coca-Cola 600ml",              "Beverages",   "https://img.example.com/coca600.jpg"),
    ("7501055305262", "Coca-Cola 355ml",              "Beverages",   "https://img.example.com/coca355.jpg"),
    ("7501055303480", "Coca-Cola Light 600ml",        "Beverages",   "https://img.example.com/cocal.jpg"),
    ("7501035901206", "Pepsi 600ml",                  "Beverages",   "https://img.example.com/pepsi.jpg"),
    ("7501035906584", "7UP 600ml",                    "Beverages",   "https://img.example.com/7up.jpg"),
    ("7501000311998", "Agua Ciel 1L",                 "Beverages",   "https://img.example.com/ciel1l.jpg"),
    ("7501000311981", "Agua Ciel 500ml",              "Beverages",   "https://img.example.com/ciel500.jpg"),
    ("7502215621049", "Boing Guayaba 500ml",          "Beverages",   "https://img.example.com/boing.jpg"),
    ("7501007910066", "Sabritas Original 45g",        "Snacks",      "https://img.example.com/sabritas.jpg"),
    ("7501007910073", "Sabritas Adobadas 45g",        "Snacks",      "https://img.example.com/sabritasado.jpg"),
    ("7501007910080", "Fritos Limón 45g",             "Snacks",      "https://img.example.com/fritos.jpg"),
    ("7501007910097", "Ruffles Queso 45g",            "Snacks",      "https://img.example.com/ruffles.jpg"),
    ("7501007910103", "Cheetos Flamin Hot 45g",       "Snacks",      "https://img.example.com/cheetos.jpg"),
    ("7506306860001", "Doritos Nacho 45g",            "Snacks",      "https://img.example.com/doritos.jpg"),
    ("7501007011001", "Takis Fuego 62g",              "Snacks",      "https://img.example.com/takis.jpg"),
    ("7503005700049", "Marinela Gansito 1pz",         "Sweets",      "https://img.example.com/gansito.jpg"),
    ("7503005700056", "Marinela Pingüinos 1pz",       "Sweets",      "https://img.example.com/pinguinos.jpg"),
    ("7501020554048", "Leche Lala Entera 1L",         "Dairy",       "https://img.example.com/lala1l.jpg"),
    ("7501020554055", "Leche Lala Semidescremada 1L", "Dairy",       "https://img.example.com/lalasemi.jpg"),
    ("7501009026615", "Yogurt Activia Natural 1kg",   "Dairy",       "https://img.example.com/activia.jpg"),
    ("7502082290000", "Jabón Zote 400g",              "Cleaning",    "https://img.example.com/zote.jpg"),
    ("7501025450003", "Detergente Ariel 1kg",         "Cleaning",    "https://img.example.com/ariel1k.jpg"),
    ("7501025450010", "Detergente Ariel 500g",        "Cleaning",    "https://img.example.com/ariel500.jpg"),
    ("7501000632011", "Fabuloso Lavanda 1L",          "Cleaning",    "https://img.example.com/fabuloso.jpg"),
    ("7501034930001", "Palomitas Act II Natural 90g", "Chips",       "https://img.example.com/actii.jpg"),
    ("7501001604018", "Arroz Morelos 1kg",            "Groceries",   "https://img.example.com/arroz.jpg"),
    ("7501001604025", "Frijol Bayo 1kg",              "Groceries",   "https://img.example.com/frijol.jpg"),
    ("7501001604032", "Azúcar Estándar 1kg",          "Groceries",   "https://img.example.com/azucar.jpg"),
    ("7501000500001", "Sal La Fina 1kg",              "Groceries",   "https://img.example.com/sal.jpg"),
    ("7501014680018", "Aceite 1-2-3 Girasol 1L",      "Groceries",   "https://img.example.com/aceite.jpg"),
]

_WEATHER: dict[str, dict] = {
    "Guadalajara":      {"base": 22, "range": 7,  "rainy_months": set(range(6, 11)), "p_rain": 0.55},
    "Ciudad de México": {"base": 17, "range": 5,  "rainy_months": set(range(6, 11)), "p_rain": 0.50},
    "Monterrey":        {"base": 25, "range": 11, "rainy_months": set(range(6, 10)), "p_rain": 0.40},
    "Puebla":           {"base": 16, "range": 5,  "rainy_months": set(range(6, 10)), "p_rain": 0.50},
    "Cancún":           {"base": 28, "range": 5,  "rainy_months": set(range(6, 11)), "p_rain": 0.65},
}

# WMO codes reales de Open-Meteo para coherencia con el entorno de producción
_WMO_CLEAR         = 0    # Cielo despejado
_WMO_PARTLY_CLOUDY = 2    # Principalmente despejado
_WMO_OVERCAST      = 3    # Cubierto
_WMO_DRIZZLE       = 51   # Llovizna: Ligera intensidad
_WMO_MODERATE_RAIN = 63   # Lluvia: Intensidad moderada
_WMO_THUNDERSTORM  = 95   # Tormenta eléctrica: Ligera o moderada

_BASE_SALES: dict[str, int] = {
    "Beverages": 15, "Snacks": 10, "Dairy": 8,
    "Cleaning": 4, "Chips": 7, "Sweets": 9, "Groceries": 6,
}
_TEMP_SENSITIVITY: dict[str, float] = {
    "Beverages": 0.55, "Snacks": 0.10, "Dairy": -0.10,
    "Cleaning": 0.00, "Chips": 0.10, "Sweets": 0.00, "Groceries": 0.05,
}
_WMO_WEATHER_FACTOR: dict[int, float] = {
    _WMO_THUNDERSTORM:  0.75,
    _WMO_MODERATE_RAIN: 0.82,
    _WMO_DRIZZLE:       0.91,
}


def _generate_weather(city: str, month: int) -> tuple[float, int]:
    """
    Genera temperatura (float) y WMO code (int) para una ciudad y mes.
    Retorna enteros WMO reales para coherencia con Open-Meteo en producción.
    """
    profile = _WEATHER[city]
    temp_offset = math.sin((month - 3) * math.pi / 6) * profile["range"]
    temperature = profile["base"] + temp_offset + random.gauss(0, 1.5)

    if month in profile["rainy_months"] and random.random() < profile["p_rain"]:
        r = random.random()
        wmo_code = (
            _WMO_DRIZZLE        if r < 0.45 else
            _WMO_MODERATE_RAIN  if r < 0.85 else
            _WMO_THUNDERSTORM
        )
    elif random.random() < 0.25:
        wmo_code = _WMO_PARTLY_CLOUDY
    elif random.random() < 0.10:
        wmo_code = _WMO_OVERCAST
    else:
        wmo_code = _WMO_CLEAR

    return round(temperature, 1), wmo_code


def _calculate_demand(
    barcode: str,
    category: str,
    current_date: date,
    temperature: float,
    wmo_code: int,
) -> int:
    """Demanda diaria con efectos realistas de temporada, quincena y clima."""
    base = _BASE_SALES.get(category, 5)
    prod_factor = (abs(hash(barcode)) % 10) / 10.0 + 0.5

    dow_factor = 1.30 if current_date.weekday() >= 5 else (1.15 if current_date.weekday() == 4 else 1.00)
    payday_factor = 1.40 if (current_date.day in range(13, 18) or current_date.day >= 27) else 1.00

    sens = _TEMP_SENSITIVITY.get(category, 0.0)
    temp_norm = (temperature - 20.0) / 15.0
    temp_factor = 1.0 + sens * temp_norm

    weather_factor = _WMO_WEATHER_FACTOR.get(wmo_code, 1.0)

    expected = base * prod_factor * dow_factor * payday_factor * temp_factor * weather_factor
    return max(1, int(np.random.poisson(max(1.0, expected))))


def _populate_stores(session) -> list[int]:
    store_ids = []
    for s in STORES:
        existing = session.query(Tienda).filter_by(email=s["email"]).first()
        if existing:
            store_ids.append(existing.store_id)
        else:
            store = Tienda(
                owner_name=s["owner_name"], email=s["email"], city=s["city"],
                latitude=s["latitude"], longitude=s["longitude"],
                registration_time=datetime.utcnow(),
            )
            session.add(store)
            session.flush()
            store_ids.append(store.store_id)
            logger.info(f"  ✅ Tienda: {s['city']} (ID={store.store_id})")
    return store_ids


def _populate_products(session) -> list[tuple[str, str]]:
    result = []
    for barcode, name, category, image in PRODUCTS:
        if not session.query(Producto).filter_by(barcode=barcode).first():
            session.add(Producto(barcode=barcode, product_name=name, category=category, image_url=image))
        result.append((barcode, category))
    logger.info(f"  ✅ {len(result)} productos listos.")
    return result


def _populate_sales(session, store_ids: list[int], products: list[tuple[str, str]], months: int) -> int:
    stores_db = {
        t.store_id: t
        for t in session.query(Tienda).filter(Tienda.store_id.in_(store_ids)).all()
    }
    start_date = date.today() - timedelta(days=months * 30)
    end_date    = date.today() - timedelta(days=1)
    total = 0
    batch: list[Venta] = []
    BATCH_SIZE = 500

    current_date = start_date
    while current_date <= end_date:
        for store_id in store_ids:
            store = stores_db[store_id]
            temperature, wmo_code = _generate_weather(store.city, current_date.month)

            n = random.randint(int(len(products) * 0.70), int(len(products) * 0.85))
            for barcode, category in random.sample(products, k=n):
                amount = _calculate_demand(barcode, category, current_date, temperature, wmo_code)
                batch.append(Venta(
                    store_id=store_id,
                    barcode=barcode,
                    date=current_date,
                    time=time(random.randint(7, 21), random.randint(0, 59)),
                    amount=amount,
                    temperature=temperature,
                    weather_resume_wmo_code=wmo_code,   # ← Integer WMO code ✅
                ))
                total += 1

            if len(batch) >= BATCH_SIZE:
                session.bulk_save_objects(batch)
                session.flush()
                batch.clear()
        current_date += timedelta(days=1)

    if batch:
        session.bulk_save_objects(batch)
    return total


def main(months: int = 3) -> None:
    logger.info("═" * 55)
    logger.info("  🔨  BanAnalytics — Data Forge (solo desarrollo)")
    logger.info(f"  Tiendas: {len(STORES)} | Productos: {len(PRODUCTS)} | Meses: {months}")
    logger.info("═" * 55)
    create_tables()
    with get_session() as session:
        logger.info("📍 Insertar tiendas...")
        store_ids = _populate_stores(session)
        logger.info("📦 Insertar productos...")
        products = _populate_products(session)
    with get_session() as session:
        logger.info("💰 Generando historial de ventas (puede tardar ~30 seg)...")
        total = _populate_sales(session, store_ids, products, months)
    logger.info(f"✅ Data Forge completado: {total:,} registros de venta generados.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="BanAnalytics — Generador de datos sintéticos.")
    parser.add_argument("--months", type=int, default=3, choices=range(1, 7), metavar="[1-6]",
                        help="Meses de historial a generar (default: 3, máx: 6).")
    args = parser.parse_args()
    main(months=args.months)