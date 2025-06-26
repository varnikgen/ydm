# ydm/app/main.py
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi import FastAPI, Form
from fastapi.middleware import Middleware
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.formparsers import MultiPartParser
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from app import models, schemas, crud, utils
from app.database import SessionLocal, engine
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse
import logging
from typing import List
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запускаем приложение
    logger.info("Starting application")
    
    # Запускаем планировщик
    scheduler.start()
    
    yield
    
    # Завершаем работу
    logger.info("Shutting down application")
    scheduler.shutdown()
    await utils.yealink_client.close()

# app = FastAPI(
#     title="Yealink Device Manager",
#     description="API для управления устройствами Yealink",
#     version="0.1.0",
#     lifespan=lifespan
# )

# Инициализация клиента Yealink
yealink_client = utils.YealinkClient()

# Определяем базовый каталог
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Инициализация логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создание таблиц в БД
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Yealink Device Manager",
    description="API для управления устройствами Yealink",
    version="0.1.0",
    middleware=[
        Middleware(TrustedHostMiddleware, allowed_hosts=["*"]),
    ],
    form_parser=MultiPartParser,  # Явно указываем обработчик форм
)


# Подключение статических файлов и шаблонов
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "..", "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация клиента Yealink
yealink_client = utils.YealinkClient()

# Роуты для веб-интерфейса
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# API роуты для устройств
@app.get("/devices/", response_model=List[schemas.Device])
def read_devices(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_devices(db, skip=skip, limit=limit)

@app.post("/devices/", response_model=schemas.Device)
def create_device_endpoint(device: schemas.DeviceCreate, db: Session = Depends(get_db)):
    return crud.create_device(db, device)

@app.get("/devices/{device_id}", response_model=schemas.Device)
def read_device(device_id: int, db: Session = Depends(get_db)):
    db_device = crud.get_device(db, device_id=device_id)
    if db_device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return db_device

@app.put("/devices/{device_id}", response_model=schemas.Device)
def update_device_endpoint(device_id: int, device: schemas.DeviceBase, db: Session = Depends(get_db)):
    return crud.update_device(db, device_id, device)

@app.delete("/devices/{device_id}")
def delete_device_endpoint(device_id: int, db: Session = Depends(get_db)):
    success = crud.delete_device(db, device_id)
    if not success:
        raise HTTPException(status_code=404, detail="Device not found")
    return {"message": "Device deleted"}

# Роуты для работы с устройствами
@app.post("/devices/{device_id}/reboot", response_model=schemas.CommandResponse)
async def reboot_device(device_id: int, db: Session = Depends(get_db)):
    db_device = crud.get_device(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    try:
        response = await yealink_client.reboot_device(db_device)
        return {
            "device_id": device_id,
            "command": "reboot",
            "response": response,
            "success": True
        }
    except Exception as e:
        logger.error(f"Reboot failed: {str(e)}")
        return {
            "device_id": device_id,
            "command": "reboot",
            "response": str(e),
            "success": False
        }

@app.get("/devices/{device_id}/status", response_model=schemas.CommandResponse)
async def get_device_status(device_id: int, db: Session = Depends(get_db)):
    db_device = crud.get_device(db, device_id)
    if not db_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    try:
        response = await yealink_client.get_status(db_device)
        return {
            "device_id": device_id,
            "command": "status",
            "response": response,
            "success": True
        }
    except Exception as e:
        logger.error(f"Status check failed: {str(e)}")
        return {
            "device_id": device_id,
            "command": "status",
            "response": str(e),
            "success": False
        }

@app.get("/devices-list", response_class=HTMLResponse)
async def devices_list(request: Request, db: Session = Depends(get_db)):
    devices = crud.get_devices(db)
    device_models = db.query(models.DeviceModel).all()
    configs = db.query(models.Config).all()
    return templates.TemplateResponse(
        "devices.html",
        {
            "request": request,
            "devices": devices,
            "device_models": device_models,
            "configs": configs
        }
    )

@app.get("/device-detail/{device_id}", response_class=HTMLResponse)
async def device_detail(request: Request, device_id: int, db: Session = Depends(get_db)):
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return templates.TemplateResponse(
        "device_detail.html",
        {"request": request, "device": device}
    )

@app.get("/device-add", response_class=HTMLResponse)
async def add_device_form(request: Request, db: Session = Depends(get_db)):
    device_models = db.query(models.DeviceModel).all()
    configs = db.query(models.Config).all()
    return templates.TemplateResponse(
        "device_form.html",
        {
            "request": request,
            "device_models": device_models,
            "configs": configs,
            "device": None # Для новой формы
        }
    )

@app.post("/device-add", response_class=HTMLResponse)
async def add_device_submit(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    
    # Обработка пустых значений для model_id и config_id
    model_id = form_data.get("model_id")
    config_id = form_data.get("config_id")
    
    device_data = schemas.DeviceCreate(
        mac_address=form_data.get("mac_address"),
        ip_address=form_data.get("ip_address"),
        username=form_data.get("username", "admin"),
        password=form_data.get("password", "admin"),
        model_id=int(model_id) if model_id else None,
        config_id=int(config_id) if config_id else None
    )
    
    #device = crud.create_device(db, device_data)
    return RedirectResponse(url="/devices-list", status_code=303)

@app.get("/device-edit/{device_id}", response_class=HTMLResponse)
async def edit_device_form(request: Request, device_id: int, db: Session = Depends(get_db)):
    device = crud.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    device_models = db.query(models.DeviceModel).all()
    configs = db.query(models.Config).all()

    return templates.TemplateResponse(
        "device_form.html",
        {
            "request": request,
            "device": device,
            "device_models": device_models,
            "configs": configs
        }
    )

@app.post("/device-edit/{device_id}", response_class=RedirectResponse)
async def edit_device_submit(device_id: int, request: Request, db: Session = Depends(get_db)):
    logger.info(f"Editing device ID: {device_id}")
    form_data = await request.form()
    
    # Обработка пустых значений
    model_id = form_data.get("model_id")
    config_id = form_data.get("config_id")
    
    device_data = schemas.DeviceBase(
        mac_address=form_data.get("mac_address"),
        ip_address=form_data.get("ip_address"),
        username=form_data.get("username"),
        password=form_data.get("password"),
        model_id=int(model_id) if model_id else None,
        config_id=int(config_id) if config_id else None
    )
    
    updated_device = crud.update_device(db, device_id, device_data)
    if not updated_device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    return RedirectResponse(url=f"/device-detail/{device_id}", status_code=303)

# Роуты для моделей устройств
@app.get("/device-models", response_model=List[schemas.DeviceModel])
def read_device_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_device_models(db, skip=skip, limit=limit)

@app.get("/device-model-list/", response_class=HTMLResponse)
async def device_models_list(request: Request, db: Session = Depends(get_db)):
    models_list = crud.get_device_models(db)
    return templates.TemplateResponse(
        "device_models.html",
        {"request": request, "device_models": models_list}
    )

@app.get("/device-model-add", response_class=HTMLResponse)
async def add_device_model_from(request: Request):
    return templates.TemplateResponse(
        "device_model_form.html",
        {"request": request,  "device_model": None}
    )

@app.post("/device-model-add", response_class=HTMLResponse)
async def add_device_model_submit(
    name: str = Form(...),
    firmware: str = Form(None),
    image: str = Form(None),
    db: Session = Depends(get_db)
):
    model_data = schemas.DeviceModelCreate(
        name=name,
        firmware=firmware,
        image=image
    )
    
    model = crud.create_device_model(db, model_data)
    return RedirectResponse(url="/device-models", status_code=303)

@app.get("/device-model-edit/{model_id}", response_class=HTMLResponse)
async def edit_device_model_form(request: Request, model_id: int, db: Session = Depends(get_db)):
    device_model = crud.get_device_model(db, model_id)
    if not device_model:
        raise HTTPException(status_code=404, detail="Device model not found")
    
    return templates.TemplateResponse(
        "device_model_form.html",
        {"request": request, "device_model": device_model}
    )

@app.post("/device-model-edit/{model_id}", response_class=HTMLResponse)
async def edit_device_model_submit(
    model_id: int,
    name: str = Form(...),
    firmware: str = Form(None),
    image: str = Form(None),
    db: Session = Depends(get_db)
):
    model_data = schemas.DeviceModelBase(
        name=name,
        firmware=firmware,
        image=image
    )
    
    updated_model = crud.update_device_model(db, model_id, model_data)
    if not updated_model:
        raise HTTPException(status_code=404, detail="Device model not found")
    
    return RedirectResponse(url="/device-models", status_code=303)

# Роуты для конфигураций
@app.get("/configs/", response_model=List[schemas.Config])
def read_configs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_configs(db, skip=skip, limit=limit)

@app.post("/configs/", response_model=schemas.Config)
def create_config_endpoint(config: schemas.ConfigCreate, db: Session = Depends(get_db)):
    return crud.create_config(db, config)

@app.get("/configs/{config_id}", response_model=schemas.Config)
def read_config(config_id: int, db: Session = Depends(get_db)):
    db_config = crud.get_config(db, config_id)
    if db_config is None:
        raise HTTPException(status_code=404, detail="Config not found")
    return db_config

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

@app.get("/config-list", response_class=HTMLResponse)
async def configs_list(request: Request, db: Session = Depends(get_db)):
    configs = crud.get_configs(db)
    return templates.TemplateResponse(
        "configs.html",
        {"request": request, "configs": configs}
    )

@app.get("/config-add", response_class=HTMLResponse)
async def add_config_form(request: Request):
    return templates.TemplateResponse(
        "config_form.html",
        {"request": request, "config": None}
    )

@app.post("/config-add", response_class=RedirectResponse)
async def add_config_submit(request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    config_data = schemas.ConfigCreate(
        name=form_data.get("name"),
        content=form_data.get("content")
    )

    config = crud.create_config(db, config_data)
    return RedirectResponse(url="/configs-list", status_code=303)

@app.get("/config-edit/{config_id}", response_class=HTMLResponse)
async def edit_config_from(request: Request, config_id: int, db: Session = Depends(get_db)):
    config = crud.get_config(db, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return templates.TemplateResponse(
        "config_form.html",
        {"request": request, "config": config}
    )

@app.post("/config-edit/{config_id}", response_class=RedirectResponse)
async def edit_config_submit(config_id: int, request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    config_data = schemas.ConfigBase(
        name=form_data.get("name"),
        content=form_data.get("content")
    )

    updated_config = crud.update_config(db, config_id, config_data)
    if not updated_config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return RedirectResponse(url="/config-list", status_code=303)

@app.post("/config-delete/{config_id}", response_class=RedirectResponse)
async def delete_config_submit(config_id: int, db: Session = Depends(get_db)):
    success = crud.delete_config(db, config_id)
    if not success:
        raise HTTPException(status_code=404, detail="Config not found")
    
    return RedirectResponse(url="/config-list", status_code=303)

@app.post("/devices/{device_id}/apply-config", response_model=schemas.CommandResponse)
async def apply_config_to_device(device_id: int, config_id: int = Form(...), db: Session = Depends(get_db)):
    device = crud.get_device(db, device_id)
    config = crud.get_config(db, config_id)
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    
    try:
        response = await yealink_client.apply_config(device, config.content)
        # Обновляем связь устройства с конфигурацией
        device.config_id = config_id
        db.commit()
        
        return {
            "device_id": device_id,
            "command": "apply_config",
            "response": response,
            "success": True
        }
    except Exception as e:
        logger.error(f"Config apply failed: {str(e)}")
        return {
            "device_id": device_id,
            "command": "apply_config",
            "response": str(e),
            "success": False
        }

async def collect_device_statuses():
    """Асинхронная функция для сбора статусов устройств"""
    with SessionLocal() as db_session:
        devices = crud.get_devices(db_session)
        for device in devices:
            try:
                async with utils.YealinkClient() as client:
                    status = await client.get_status(device)
                    device.last_status = status
                    db_session.add(device)
                    db_session.commit()
            except Exception as e:
                logger.error(f"Failed to get status for device {device.id}: {str(e)}")

# Планировщик задач
scheduler = AsyncIOScheduler()
scheduler.add_job(
    collect_device_statuses,
    'interval',
    minutes=10
)

# Запускаем планировщик при старте приложения
@app.on_event("startup")
async def startup_event():
    scheduler.start()

# Остановка планировщика при завершении приложения
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
