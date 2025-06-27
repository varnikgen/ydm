# ydm/app/crud.py
from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime, timezone

# По работе с моделями устройств
def create_device_model(db: Session, model: schemas.DeviceModelCreate):
    db_model = models.DeviceModel(**model.model_dump())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_device_model(db: Session, model_id: int):
    return db.query(models.DeviceModel).filter(models.DeviceModel.id == model_id).first()

def get_device_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.DeviceModel).offset(skip).limit(limit).all()

def update_device_model(db: Session, model_id: int, model_data: schemas.DeviceModelBase):
    db_model = db.query(models.DeviceModel).filter(models.DeviceModel.id == model_id).first()
    if not db_model:
        return None
    
    update_data = model_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_model, key, value)
    
    db.commit()
    db.refresh(db_model)
    return db_model

def delete_device_model(db: Session, model_id: int):
    db_model = db.query(models.DeviceModel).filter(models.DeviceModel.id == model_id).first()
    if db_model:
        db.delete(db_model)
        db.commit()
        return True
    return False

# По работе с устройствами
def create_device(db: Session, device: schemas.DeviceCreate):

    # Создаём словарь данных, исключая необязательные поля
    device_data = device.model_dump(exclude_unset=True)

    # Удаляем config_id и model_id, если они None
    for field in ["config_id", "model_id"]:
        if field in device_data and device_data[field] is None:
            del device_data[field]

    # Создаём объект устройства
    db_device = models.Device(**device_data)
    
    db.add(db_device)
    db.commit()
    db.refresh(db_device)
    return db_device

def get_device(db: Session, device_id: int):
    return db.query(models.Device).filter(models.Device.id == device_id).first()

def get_device_by_mac(db: Session, mac_address: str):
    return db.query(models.Device).filter(models.Device.mac_address == mac_address).first()

def get_devices(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Device).offset(skip).limit(limit).all()

def update_device(db: Session, device_id: int, device_data: schemas.DeviceBase):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if not db_device:
        return None
    
    update_data = device_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_device, key, value)
    
    db.commit()
    db.refresh(db_device)
    return db_device

def delete_device(db: Session, device_id: int):
    db_device = db.query(models.Device).filter(models.Device.id == device_id).first()
    if db_device:
        db.delete(db_device)
        db.commit()
        return True
    return False

# По работе с конфигами
def create_config(db: Session, config: schemas.ConfigCreate):
    db_config = models.Config(**config.model_dump())
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config

def get_configs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Config).offset(skip).limit(limit).all()

def get_config(db: Session, config_id: int):
    return db.query(models.Config).filter(models.Config.id == config_id).first()

def update_config(db: Session, config_id: int, config_data: schemas.ConfigBase):
    db_config = db.query(models.Config).filter(models.Config.id == config_id).first()
    if not db_config:
        return None
    
    update_data = config_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_config, key, value)
    
    db.commit()
    db.refresh(db_config)
    return db_config

def delete_config(db: Session, config_id: int):
    db_config = db.query(models.Config).filter(models.Config.id == config_id).first()
    if db_config:
        # Сначала отвязываем устройства от конфигурации
        db.query(models.Device).filter(models.Device.config_id == config_id).update({models.Device.config_id: None})
        db.delete(db_config)
        db.commit()
        return True
    return False
