# ydm/app/models.py
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class DeviceModel(Base):
    __tablename__ = "device_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True)  # Название модели (T54S, T58V и т.д.)
    firmware = Column(String(20))  # Версия прошивки
    image = Column(String(255))    # URL изображения модели

class Device(Base):
    __tablename__ = "devices"
    
    id = Column(Integer, primary_key=True, index=True)
    mac_address = Column(String(17), unique=True, index=True)
    ip_address = Column(String(15))
    username = Column(String(50), default="admin")  # Для аутентификации
    password = Column(String(50), default="admin")   # Для аутентификации
    last_status = Column(Text)  # JSON-строка с последним статусом
    config_id = Column(Integer, ForeignKey("configs.id"))
    model_id = Column(Integer, ForeignKey("device_models.id"))  # Связь с моделью
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Исправлено: back_populates вместо black_populates
    config = relationship("Config", back_populates="devices")
    model = relationship("DeviceModel")

class Config(Base):
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True)
    content = Column(Text)  # XML-конфигурация Yealink
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    devices = relationship("Device", back_populates="config")
    