"""
Modelos ORM de SQLAlchemy para BanAnalytics.

Tablas mapeadas (esquema del documento de Arquitectura):
  · stores_database     → Tienda
  · product_database    → Producto
  · sales_database      → Venta
  · prediction_database → Prediccion  (incluye store_id, percentage_average_deviation,
                                        avg_weekly_sales y margin_of_error)
  · models_database     → ModeloML

Decisiones de diseño:
  - BigInteger en sale_id y prediction.id por volumen esperado a largo plazo.
  - ENUM de PostgreSQL para TipoAlerta (integridad sin validación en app).
  - UniqueConstraint en Prediccion(store_id, barcode, objective_date).
  - weather_resume_wmo_code: Integer WMO — coherencia con Open-Meteo en producción.
  - prediction: Integer — las unidades a vender son siempre enteras.
  - percentage_average_deviation: Float — variación % para diagnóstico y frontend.
  - avg_weekly_sales: Int — promedio semanal de ventas del último mes (diario × 7).
    Permite al cliente final contextualizar la predicción frente al ritmo habitual.
  - margin_of_error: Integer — RMSE del modelo redondeado a unidades del producto.
    Expresa el desvío típico: la venta real estará en el rango
    [prediction − margin_of_error, prediction + margin_of_error].
  - last_rmse (ModeloML): RMSE = √MSE, directamente interpretable en unidades
    del producto. Reemplaza last_mse para mayor claridad semántica y coherencia
    con margin_of_error en prediction_database.
"""

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger, Boolean, Column, Date, DateTime, Enum,
    Float, ForeignKey, Index, Integer, LargeBinary,
    String, Time, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class TipoAlerta(str, enum.Enum):
    superavit = "superavit"
    deficit   = "deficit"
    none      = "none"


class Tienda(Base):
    __tablename__ = "stores_database"

    store_id          = Column(Integer,      primary_key=True, autoincrement=True)
    owner_name        = Column(String(255),  nullable=False)
    email             = Column(String(255),  nullable=False, unique=True)
    city              = Column(String(100),  nullable=False)
    latitude          = Column(Float,        nullable=False)
    longitude         = Column(Float,        nullable=False)
    registration_time = Column(DateTime,     default=datetime.utcnow, nullable=False)

    ventas       = relationship("Venta",      back_populates="tienda",  lazy="select")
    predicciones = relationship("Prediccion", back_populates="tienda",  lazy="select")

    def __repr__(self) -> str:
        return f"<Tienda id={self.store_id} ciudad='{self.city}'>"


class Producto(Base):
    __tablename__ = "product_database"

    barcode      = Column(String(50),  primary_key=True)
    product_name = Column(String(255), nullable=False)
    category     = Column(String(100))
    image_url    = Column(String(500))

    ventas       = relationship("Venta",      back_populates="producto", lazy="select")
    modelo       = relationship("ModeloML",   back_populates="producto", uselist=False, lazy="select")
    predicciones = relationship("Prediccion", back_populates="producto", lazy="select")

    def __repr__(self) -> str:
        return f"<Producto barcode='{self.barcode}' nombre='{self.product_name}'>"


class Venta(Base):
    __tablename__ = "sales_database"
    __table_args__ = (
        Index("ix_ventas_barcode_date", "barcode", "date"),
        Index("ix_ventas_store_date",   "store_id", "date"),
    )

    sale_id                 = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id                = Column(Integer,    ForeignKey("stores_database.store_id"), nullable=False)
    barcode                 = Column(String(50), ForeignKey("product_database.barcode"), nullable=False)
    date                    = Column(Date,    nullable=False)
    time                    = Column(Time,    nullable=False)
    amount                  = Column(Integer, nullable=False)
    temperature             = Column(Float)   # NULL si la API no pudo recabar la información
    weather_resume_wmo_code = Column(Integer) # Código WMO real; NULL si offline

    tienda   = relationship("Tienda",   back_populates="ventas")
    producto = relationship("Producto", back_populates="ventas")

    def __repr__(self) -> str:
        return f"<Venta id={self.sale_id} barcode='{self.barcode}' date={self.date}>"


class Prediccion(Base):
    __tablename__ = "prediction_database"
    __table_args__ = (
        UniqueConstraint(
            "store_id", "barcode", "objective_date",
            name="uq_prediccion_tienda_producto_fecha",
        ),
    )

    id       = Column(BigInteger, primary_key=True, autoincrement=True)
    store_id = Column(Integer,    ForeignKey("stores_database.store_id"), nullable=False, index=True)
    barcode  = Column(String(50), ForeignKey("product_database.barcode"), nullable=False, index=True)

    # Campos desnormalizados para evitar JOINs en el cliente local
    product_name = Column(String(255))
    category     = Column(String(100))
    image_url    = Column(String(500))

    objective_date               = Column(Date,    nullable=False)
    prediction                   = Column(Integer, nullable=False)       # Unidades enteras
    feature                      = Column(Boolean, default=False, nullable=False)  # es_destacado
    type                         = Column(Enum(TipoAlerta, name="tipo_alerta"), default=TipoAlerta.none, nullable=False)
    percentage_average_deviation = Column(Float,   nullable=False)       # Variación % RF-05

    # ── Contexto de ventas y calidad del modelo ───────────────────────────────
    avg_weekly_sales = Column(Integer,   nullable=False, default=0)
    # Promedio de ventas semanales del último mes para esta (tienda, producto).
    # Base de referencia que el cliente usa para interpretar la predicción
    # en el contexto del volumen habitual del negocio.

    margin_of_error  = Column(Integer, nullable=False, default=0)
    # RMSE del modelo en unidades del producto, redondeado al entero más próximo.
    # Rango de confianza de la predicción:
    #   ventas_reales ∈ [prediction − margin_of_error, prediction + margin_of_error]

    tienda   = relationship("Tienda",   back_populates="predicciones")
    producto = relationship("Producto", back_populates="predicciones")

    def __repr__(self) -> str:
        return (
            f"<Prediccion store={self.store_id} barcode='{self.barcode}' "
            f"fecha={self.objective_date} pred={self.prediction} "
            f"±{self.margin_of_error} avg_semanal={self.avg_weekly_sales:.1f}>"
        )


class ModeloML(Base):
    __tablename__ = "models_database"

    model_id       = Column(Integer,    primary_key=True, autoincrement=True)
    barcode        = Column(String(50), ForeignKey("product_database.barcode"),
                            nullable=False, unique=True, index=True)
    binary_model   = Column(LargeBinary)
    last_update    = Column(DateTime)
    total_examples = Column(Integer, default=0)
    last_rmse      = Column(Float)
    # RMSE = √MSE: error cuadrático medio del modelo expresado en unidades del
    # producto. Directamente coherente con margin_of_error en prediction_database.
    type_model     = Column(String(50), default="SGDRegressor-v2", nullable=False)

    producto = relationship("Producto", back_populates="modelo")

    def __repr__(self) -> str:
        return (
            f"<ModeloML barcode='{self.barcode}' "
            f"ejemplos={self.total_examples} rmse={self.last_rmse}>"
        )
