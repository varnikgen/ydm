# ydm/app/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class DeviceModelBase(BaseModel):
    name: str = Field(..., example="T54S")
    firmware: Optional[str] = Field(None, example="96.86.0.5")
    image: Optional[str] = Field(None, example="/static/images/t54s.png")

class DeviceModelCreate(DeviceModelBase):
    pass

class DeviceModel(DeviceModelBase):
    id: int

    model_config = ConfigDict(from_attributes=True)

class DeviceBase(BaseModel):
    mac_address: str = Field(..., example="00:15:65:XX:XX:XX")
    ip_address: str = Field(..., example="192.168.1.100")
    username: str = Field("admin", example="admin")
    password: str = Field("admin", example="admin")
    config_id: Optional[int] = None
    model_id: Optional[int] = None

class DeviceCreate(DeviceBase):
    pass

class Device(DeviceBase):
    id: int
    last_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    config: Optional["Config"] = None
    model: Optional[DeviceModel] = None

    model_config = ConfigDict(from_attributes=True)

class ConfigBase(BaseModel):
    name: str = Field(..., example="Office Default")
    content: str = Field(..., example="<YealinkIPPhoneConfiguration>...</YealinkIPPhoneConfiguration>")

class ConfigCreate(ConfigBase):
    pass

class Config(ConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DeviceStatus(BaseModel):
    status: str
    details: Optional[dict] = None

class CommandResponse(BaseModel):
    device_id: int
    command: str
    response: str
    success: bool
