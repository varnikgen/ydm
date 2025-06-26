import httpx
from fastapi import HTTPException
from .models import Device

class YealinkClient:
    def __init__(self):
        # Создаем клиент с отключенной SSL-проверкой
        self.client = httpx.AsyncClient(verify=False)

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def send_command(self, device: Device, query: str, command: str, params: dict = None):
        """Отправка команды на устройство Yealink с аутентификацией"""
        base_url = f"https://{device.ip_address}/servlet"
        query_params = {query: command}
        
        if params:
            query_params.update(params)
        
        try:
            # Добавляем Basic Auth
            auth = (device.username, device.password)
            response = await self.client.get(
                base_url,
                params=query_params,
                auth=auth,
                timeout=10.0
            )
            response.raise_for_status()
            return response.text
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Device communication error: {str(e)}"
            )
    
    async def get_status(self, device: Device):
        """Получение статуса устройства с дополнительными параметрами"""
        return await self.send_command(
            device, 
            "phonecfg", 
            "get",
            {"accounts": "1", "dnd": "1", "fw": "1"}
        )
    
    async def reboot_device(self, device: Device):
        """Перезагрузка устройства"""
        return await self.send_command(device, "key", "Reboot")
    
    async def apply_config(self, device: Device, config_content: str):
        """Применение конфигурации к устройству"""
        base_url = f"https://{device.ip_address}/servlet"
        try:
            auth = (device.username, device.password)
            response = await self.client.post(
                base_url,
                content=config_content,
                auth=auth,
                timeout=30.0,
                headers={"Content-Type": "application/xml"}
            )
            response.raise_for_status()
            return response.text
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка применения конфигурации: {str(e)}"
            )
    
    async def close(self):
        """Закрыть клиент при завершении"""
        await self.client.aclose()