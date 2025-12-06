"""Hardware Interface Tool для LangGraph"""
from typing import Dict, Any, Literal
from agents.hardware.interface import hardware_interface, PrinterStatus


class HardwareTool:
    """Инструмент для управления принтером"""
    
    def __init__(self):
        self.interface = hardware_interface
    
    async def get_status(self) -> Dict[str, Any]:
        """Получить статус принтера"""
        status: PrinterStatus = await self.interface.get_status()
        
        return {
            "state": status.state,
            "current_temp": status.current_temp,
            "target_temp": status.target_temp,
            "bed_temp": status.bed_temp,
            "bed_target": status.bed_target,
            "extruder_position": status.extruder_position,
            "print_progress": status.print_progress,
            "current_file": status.current_file,
            "estimated_time": status.estimated_time,
            "print_duration": status.print_duration,
            "print_time_remaining": status.print_time_remaining,
            "api_type": self.interface.api_type
        }
    
    async def get_temperature(self) -> Dict[str, float]:
        """Получить температуры"""
        status = await self.get_status()
        return {
            "bed": status["bed_temp"],
            "nozzle": status["current_temp"],
            "bed_target": status["bed_target"],
            "nozzle_target": status["target_temp"]
        }
    
    async def set_temperature(self, bed_temp: float = None, nozzle_temp: float = None) -> bool:
        """Установить температуру"""
        success = True
        
        if bed_temp is not None:
            result = await self.interface.set_temperature(bed_temp, bed=True)
            success = success and result
        
        if nozzle_temp is not None:
            result = await self.interface.set_temperature(nozzle_temp, bed=False)
            success = success and result
        
        return success
    
    async def start_print(self, gcode_file: str) -> bool:
        """Начать печать"""
        return await self.interface.start_print(gcode_file)
    
    async def stop_print(self) -> bool:
        """Остановить печать"""
        return await self.interface.cancel_print()
    
    async def pause_print(self) -> bool:
        """Приостановить печать"""
        return await self.interface.pause_print()
    
    async def resume_print(self) -> bool:
        """Возобновить печать"""
        return await self.interface.resume_print()
    
    async def home_axes(self, axes: str = "XYZ") -> bool:
        """Домой оси"""
        return await self.interface.home_axes(axes)
    
    def get_tool_description(self) -> str:
        """Описание инструмента для LLM"""
        return f"""Hardware Interface Tool для управления принтером ({self.interface.api_type}):
        - get_status: Получить полный статус принтера (температура, прогресс, состояние)
        - get_temperature: Получить текущие температуры стола и сопла
        - set_temperature: Установить температуру стола и/или сопла
        - start_print: Начать печать G-code файла
        - stop_print: Остановить печать
        - pause_print: Приостановить печать
        - resume_print: Возобновить печать
        - home_axes: Домой оси
        """


hardware_tool = HardwareTool()
