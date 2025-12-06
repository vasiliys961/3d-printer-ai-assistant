"""Интеграция с реальным принтером через API.

Поддерживаемые API:
- Klipper/Moonraker (новый стандарт, рекомендуется)
- OctoPrint (классический, для старых систем)
- Bambu Lab Cloud API (если доступ есть)
"""

import asyncio
from typing import Optional, Dict, List
from dataclasses import dataclass
import aiohttp
from config import settings


@dataclass
class PrinterStatus:
    """Статус принтера"""
    state: str  # "printing", "idle", "paused", "error"
    current_temp: float
    target_temp: float
    bed_temp: float
    bed_target: float
    extruder_position: float
    print_progress: float  # 0-100
    current_file: Optional[str]
    estimated_time: Optional[float]
    print_duration: Optional[float]  # секунды
    print_time_remaining: Optional[float]  # секунды


class HardwareInterface:
    """Интерфейс с реальным оборудованием"""
    
    def __init__(self, api_type: str = None, endpoint: str = None):
        """
        Args:
            api_type: "moonraker" или "octoprint"
            endpoint: URL API
        """
        # Определяем тип API из конфига
        if api_type is None:
            if settings.klipper_api_url:
                self.api_type = "moonraker"
                self.endpoint = settings.klipper_api_url
            elif settings.octoprint_api_url:
                self.api_type = "octoprint"
                self.endpoint = settings.octoprint_api_url
            else:
                self.api_type = "moonraker"
                self.endpoint = "http://localhost:7125"
        else:
            self.api_type = api_type
            self.endpoint = endpoint or "http://localhost:7125"
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = settings.octoprint_api_key if self.api_type == "octoprint" else None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать сессию"""
        if self.session is None or self.session.closed:
            headers = {}
            if self.api_key:
                headers["X-Api-Key"] = self.api_key
            self.session = aiohttp.ClientSession(headers=headers, timeout=aiohttp.ClientTimeout(total=10))
        return self.session
    
    async def close(self):
        """Закрыть сессию"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def get_status(self) -> PrinterStatus:
        """Получить статус принтера"""
        if self.api_type == "moonraker":
            return await self._get_moonraker_status()
        elif self.api_type == "octoprint":
            return await self._get_octoprint_status()
        else:
            raise ValueError(f"Unsupported API type: {self.api_type}")
    
    async def _get_moonraker_status(self) -> PrinterStatus:
        """Запрос статуса через Moonraker API"""
        session = await self._get_session()
        
        try:
            # Moonraker эндпоинты
            printer = await self._moonraker_rpc(session, "printer.objects.query", {
                "objects": {
                    "extruder": ["temperature", "target", "power"],
                    "heater_bed": ["temperature", "target"],
                    "print_stats": ["state", "filename", "print_duration", "total_duration"],
                    "display_status": ["progress"],
                    "toolhead": ["position"]
                }
            })
            
            status = printer.get("result", {}).get("status", {})
            print_stats = status.get("print_stats", {})
            extruder = status.get("extruder", {})
            heater_bed = status.get("heater_bed", {})
            display_status = status.get("display_status", {})
            toolhead = status.get("toolhead", {})
            
            state = print_stats.get("state", "unknown")
            print_duration = print_stats.get("print_duration", 0)
            total_duration = print_stats.get("total_duration", 0)
            
            # Вычисляем прогресс
            progress = display_status.get("progress", 0) * 100 if display_status.get("progress") else 0
            
            # Вычисляем оставшееся время
            time_remaining = None
            if progress > 0 and print_duration > 0:
                time_remaining = (print_duration / progress * 100) - print_duration
            
            # Позиция экструдера (E axis)
            position = toolhead.get("position", [0, 0, 0, 0])
            extruder_position = position[3] if len(position) > 3 else 0
            
            return PrinterStatus(
                state=state,
                current_temp=extruder.get("temperature", 0),
                target_temp=extruder.get("target", 0),
                bed_temp=heater_bed.get("temperature", 0),
                bed_target=heater_bed.get("target", 0),
                extruder_position=extruder_position,
                print_progress=progress,
                current_file=print_stats.get("filename"),
                estimated_time=total_duration,
                print_duration=print_duration,
                print_time_remaining=time_remaining
            )
        except Exception as e:
            # Возвращаем статус по умолчанию при ошибке
            return PrinterStatus(
                state="error",
                current_temp=0,
                target_temp=0,
                bed_temp=0,
                bed_target=0,
                extruder_position=0,
                print_progress=0,
                current_file=None,
                estimated_time=None,
                print_duration=None,
                print_time_remaining=None
            )
    
    async def _get_octoprint_status(self) -> PrinterStatus:
        """Запрос статуса через OctoPrint API"""
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.endpoint}/api/printer") as resp:
                if resp.status != 200:
                    raise Exception(f"OctoPrint API error: {resp.status}")
                
                data = await resp.json()
                temperature = data.get("temperature", {})
                state = data.get("state", {})
                
                # Получаем информацию о задании
                async with session.get(f"{self.endpoint}/api/job") as job_resp:
                    job_data = await resp.json() if job_resp.status == 200 else {}
                    job = job_data.get("job", {})
                    progress = job_data.get("progress", {})
                
                tool0 = temperature.get("tool0", {})
                bed = temperature.get("bed", {})
                
                return PrinterStatus(
                    state=state.get("text", "unknown"),
                    current_temp=tool0.get("actual", 0),
                    target_temp=tool0.get("target", 0),
                    bed_temp=bed.get("actual", 0),
                    bed_target=bed.get("target", 0),
                    extruder_position=0,  # OctoPrint не предоставляет напрямую
                    print_progress=progress.get("completion", 0),
                    current_file=job.get("file", {}).get("name"),
                    estimated_time=progress.get("printTimeLeft"),
                    print_duration=progress.get("printTime"),
                    print_time_remaining=progress.get("printTimeLeft")
                )
        except Exception as e:
            return PrinterStatus(
                state="error",
                current_temp=0,
                target_temp=0,
                bed_temp=0,
                bed_target=0,
                extruder_position=0,
                print_progress=0,
                current_file=None,
                estimated_time=None,
                print_duration=None,
                print_time_remaining=None
            )
    
    async def _moonraker_rpc(self, session: aiohttp.ClientSession, method: str, params: Dict):
        """RPC запрос к Moonraker"""
        # Moonraker использует /jsonrpc для RPC запросов
        async with session.post(
            f"{self.endpoint}/jsonrpc",
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
        ) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                # Fallback на альтернативный эндпоинт если есть
                try:
                    async with session.post(
                        f"{self.endpoint}/printer/gcode/script",
                        json={"script": f"{method} {params}"}
                    ) as resp2:
                        return {"result": "ok"} if resp2.status == 200 else {"error": "Failed"}
                except:
                    return {"error": f"HTTP {resp.status}"}
    
    async def start_print(self, filename: str) -> bool:
        """Запустить печать файла"""
        if self.api_type == "moonraker":
            return await self._moonraker_start_print(filename)
        elif self.api_type == "octoprint":
            return await self._octoprint_start_print(filename)
        return False
    
    async def _moonraker_start_print(self, filename: str) -> bool:
        """Запуск печати через Moonraker"""
        session = await self._get_session()
        try:
            # Moonraker использует printer.print.start для запуска печати
            result = await self._moonraker_rpc(session, "printer.print.start", {
                "filename": filename
            })
            # Проверяем результат RPC запроса
            if "result" in result:
                return result.get("result") == "ok"
            # Альтернативный способ через G-code
            async with session.post(
                f"{self.endpoint}/printer/print/start",
                json={"filename": filename}
            ) as resp:
                return resp.status == 200
        except Exception:
            return False
    
    async def _octoprint_start_print(self, filename: str) -> bool:
        """Запуск печати через OctoPrint"""
        session = await self._get_session()
        try:
            async with session.post(
                f"{self.endpoint}/api/files/local/{filename}",
                json={"command": "select", "print": True}
            ) as resp:
                return resp.status == 204
        except Exception:
            return False
    
    async def pause_print(self) -> bool:
        """Пауза печати"""
        if self.api_type == "moonraker":
            session = await self._get_session()
            try:
                result = await self._moonraker_rpc(session, "printer.print.pause", {})
                return result.get("result") == "ok"
            except Exception:
                return False
        elif self.api_type == "octoprint":
            session = await self._get_session()
            try:
                async with session.post(
                    f"{self.endpoint}/api/job",
                    json={"command": "pause", "action": "pause"}
                ) as resp:
                    return resp.status == 204
            except Exception:
                return False
        return False
    
    async def resume_print(self) -> bool:
        """Возобновить печать"""
        if self.api_type == "moonraker":
            session = await self._get_session()
            try:
                result = await self._moonraker_rpc(session, "printer.print.resume", {})
                return result.get("result") == "ok"
            except Exception:
                return False
        elif self.api_type == "octoprint":
            session = await self._get_session()
            try:
                async with session.post(
                    f"{self.endpoint}/api/job",
                    json={"command": "pause", "action": "resume"}
                ) as resp:
                    return resp.status == 204
            except Exception:
                return False
        return False
    
    async def cancel_print(self) -> bool:
        """Отмена печати"""
        if self.api_type == "moonraker":
            session = await self._get_session()
            try:
                result = await self._moonraker_rpc(session, "printer.print.cancel", {})
                return result.get("result") == "ok"
            except Exception:
                return False
        elif self.api_type == "octoprint":
            session = await self._get_session()
            try:
                async with session.post(
                    f"{self.endpoint}/api/job",
                    json={"command": "cancel"}
                ) as resp:
                    return resp.status == 204
            except Exception:
                return False
        return False
    
    async def set_temperature(self, temp: float, bed: bool = False) -> bool:
        """Установить температуру сопла или стола"""
        if self.api_type == "moonraker":
            session = await self._get_session()
            try:
                heater = "heater_bed" if bed else "extruder"
                # Используем G-code команду через printer/gcode/script
                async with session.post(
                    f"{self.endpoint}/printer/gcode/script",
                    json={"script": f"SET_HEATER_TEMPERATURE HEATER={heater} TARGET={temp}"}
                ) as resp:
                    return resp.status == 200
            except Exception:
                return False
        elif self.api_type == "octoprint":
            session = await self._get_session()
            try:
                endpoint = f"{self.endpoint}/api/printer/bed" if bed else f"{self.endpoint}/api/printer/tool"
                async with session.post(
                    endpoint,
                    json={"command": "target", "target": temp} if bed else {"command": "target", "targets": {"tool0": temp}}
                ) as resp:
                    return resp.status == 204
            except Exception:
                return False
        return False
    
    async def home_axes(self, axes: str = "XYZ") -> bool:
        """Домой оси"""
        if self.api_type == "moonraker":
            session = await self._get_session()
            try:
                # Используем G-code команду через printer/gcode/script
                async with session.post(
                    f"{self.endpoint}/printer/gcode/script",
                    json={"script": f"G28 {axes}"}
                ) as resp:
                    return resp.status == 200
            except Exception:
                return False
        elif self.api_type == "octoprint":
            session = await self._get_session()
            try:
                axes_list = [ax.lower() for ax in axes]
                async with session.post(
                    f"{self.endpoint}/api/printer/printhead",
                    json={"command": "home", "axes": axes_list}
                ) as resp:
                    return resp.status == 204
            except Exception:
                return False
        return False


# Создаем глобальный экземпляр
hardware_interface = HardwareInterface()

