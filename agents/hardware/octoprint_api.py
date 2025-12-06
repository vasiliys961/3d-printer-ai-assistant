"""OctoPrint API клиент"""
import httpx
from typing import Dict, Optional, Any
from config import settings


class OctoPrintAPI:
    """Клиент для работы с OctoPrint API"""
    
    def __init__(self):
        self.base_url = settings.octoprint_api_url
        self.api_key = settings.octoprint_api_key
        self.client = httpx.AsyncClient(
            timeout=10.0,
            headers={"X-Api-Key": self.api_key} if self.api_key else {}
        )
    
    async def get_printer_status(self) -> Dict[str, Any]:
        """Получить статус принтера"""
        try:
            response = await self.client.get(f"{self.base_url}/api/printer")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_temperature(self) -> Dict[str, float]:
        """Получить текущие температуры"""
        status = await self.get_printer_status()
        if "temperature" in status:
            temp = status["temperature"]
            return {
                "bed": temp.get("bed", {}).get("actual", 0),
                "nozzle": temp.get("tool0", {}).get("actual", 0),
            }
        return {"bed": 0, "nozzle": 0}
    
    async def set_temperature(self, bed_temp: float = None, nozzle_temp: float = None) -> bool:
        """Установить температуру"""
        try:
            if bed_temp is not None:
                await self.client.post(
                    f"{self.base_url}/api/printer/bed",
                    json={"command": "target", "target": bed_temp}
                )
            if nozzle_temp is not None:
                await self.client.post(
                    f"{self.base_url}/api/printer/tool",
                    json={"command": "target", "targets": {"tool0": nozzle_temp}}
                )
            return True
        except Exception:
            return False
    
    async def start_print(self, gcode_file: str) -> bool:
        """Начать печать"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/files/local/{gcode_file}",
                json={"command": "select", "print": True}
            )
            return response.status_code == 204
        except Exception:
            return False
    
    async def stop_print(self) -> bool:
        """Остановить печать"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job",
                json={"command": "cancel"}
            )
            return response.status_code == 204
        except Exception:
            return False
    
    async def pause_print(self) -> bool:
        """Приостановить печать"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job",
                json={"command": "pause", "action": "pause"}
            )
            return response.status_code == 204
        except Exception:
            return False
    
    async def resume_print(self) -> bool:
        """Возобновить печать"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/job",
                json={"command": "pause", "action": "resume"}
            )
            return response.status_code == 204
        except Exception:
            return False
    
    async def home_axes(self, axes: list = None) -> bool:
        """Домой оси"""
        try:
            axes = axes or ["x", "y", "z"]
            response = await self.client.post(
                f"{self.base_url}/api/printer/printhead",
                json={"command": "home", "axes": axes}
            )
            return response.status_code == 204
        except Exception:
            return False
    
    async def close(self):
        """Закрыть клиент"""
        await self.client.aclose()


octoprint_api = OctoPrintAPI()

