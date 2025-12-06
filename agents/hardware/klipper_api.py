"""Klipper/Moonraker API клиент"""
import httpx
from typing import Dict, Optional, Any
from config import settings


class KlipperAPI:
    """Клиент для работы с Klipper через Moonraker API"""
    
    def __init__(self):
        self.base_url = settings.klipper_api_url
        self.client = httpx.AsyncClient(timeout=10.0)
    
    async def get_printer_status(self) -> Dict[str, Any]:
        """Получить статус принтера"""
        try:
            response = await self.client.get(f"{self.base_url}/printer/objects/query?heater_bed&extruder&print_stats")
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    async def get_temperature(self) -> Dict[str, float]:
        """Получить текущие температуры"""
        status = await self.get_printer_status()
        if "result" in status:
            data = status["result"]["status"]
            return {
                "bed": data.get("heater_bed", {}).get("temperature", 0),
                "nozzle": data.get("extruder", {}).get("temperature", 0),
            }
        return {"bed": 0, "nozzle": 0}
    
    async def set_temperature(self, bed_temp: float = None, nozzle_temp: float = None) -> bool:
        """Установить температуру"""
        try:
            commands = []
            if bed_temp is not None:
                commands.append(f"SET_HEATER_TEMPERATURE HEATER=heater_bed TARGET={bed_temp}")
            if nozzle_temp is not None:
                commands.append(f"SET_HEATER_TEMPERATURE HEATER=extruder TARGET={nozzle_temp}")
            
            if commands:
                response = await self.client.post(
                    f"{self.base_url}/printer/gcode/script",
                    json={"script": "\n".join(commands)}
                )
                return response.status_code == 200
        except Exception:
            pass
        return False
    
    async def start_print(self, gcode_file: str) -> bool:
        """Начать печать"""
        try:
            response = await self.client.post(
                f"{self.base_url}/printer/print/start",
                json={"filename": gcode_file}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def stop_print(self) -> bool:
        """Остановить печать"""
        try:
            response = await self.client.post(f"{self.base_url}/printer/print/cancel")
            return response.status_code == 200
        except Exception:
            return False
    
    async def pause_print(self) -> bool:
        """Приостановить печать"""
        try:
            response = await self.client.post(f"{self.base_url}/printer/print/pause")
            return response.status_code == 200
        except Exception:
            return False
    
    async def resume_print(self) -> bool:
        """Возобновить печать"""
        try:
            response = await self.client.post(f"{self.base_url}/printer/print/resume")
            return response.status_code == 200
        except Exception:
            return False
    
    async def home_axes(self, axes: str = "XYZ") -> bool:
        """Домой оси"""
        try:
            response = await self.client.post(
                f"{self.base_url}/printer/gcode/script",
                json={"script": f"G28 {axes}"}
            )
            return response.status_code == 200
        except Exception:
            return False
    
    async def close(self):
        """Закрыть клиент"""
        await self.client.aclose()


klipper_api = KlipperAPI()

