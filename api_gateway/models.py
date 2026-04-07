from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, DATE, TIME, ForeignKey, Boolean, Float, LargeBinary
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Store(Base):
    __tablename__ = "stores_database"
    
    store_id = Column(Integer, primary_key=True, index=True)
    owner_name = Column(String)
    email = Column(String, unique=True)
    city = Column(String)
    latitude = Column(DECIMAL)
    longitude = Column(DECIMAL)
    registration_time = Column(TIMESTAMP)

class Product(Base):
    __tablename__ = "products_database"
    
    barcode = Column(String, primary_key=True, index=True)
    product_name = Column(String)
    category = Column(String)
    image_url = Column(String)

class Sale(Base):
    __tablename__ = "sales_database"
    
    sale_id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores_database.store_id"))
    barcode = Column(String, ForeignKey("products_database.barcode"))
    date = Column(DATE)
    time = Column(TIME)
    amount = Column(Integer)
    temperature = Column(DECIMAL)
    weather_resume = Column(String)

class Prediction(Base):
    __tablename__ = "prediction_database"
    
    id_prediction = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores_database.store_id")) 
    barcode = Column(String, ForeignKey("products_database.barcode"))
    objetive_date = Column(DATE)
    prediction = Column(Integer)
    feature = Column(Boolean)
    type = Column(String)
    percentage_average_deviation = Column(Float)

class Model(Base):
    __tablename__ = "models_database"
    
    model_id = Column(Integer, primary_key=True, index=True)
    binary_model = Column(BYTEA) 
    last_update = Column(TIMESTAMP)
    total_examples = Column(Integer)
    last_mse = Column(Float)
    barcode = Column(String, ForeignKey("products_database.barcode"))
    type_model = Column(String)