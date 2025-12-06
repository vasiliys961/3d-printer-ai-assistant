"""G-code Generator"""
from typing import List, Dict
from agents.code_interpreter.parser import GCodeCommand


class GCodeGenerator:
    """Генератор G-code последовательностей"""
    
    def generate_start_sequence(self, bed_temp: float = 60, nozzle_temp: float = 200) -> List[str]:
        """Генерация стартовой последовательности"""
        sequence = [
            "G28 ; Home all axes",
            f"M140 S{bed_temp} ; Set bed temperature",
            f"M104 S{nozzle_temp} ; Set nozzle temperature",
            "M190 S60 ; Wait for bed temperature",
            f"M109 S{nozzle_temp} ; Wait for nozzle temperature",
            "G92 E0 ; Reset extruder",
            "G1 Z0.2 F3000 ; Move to layer height",
        ]
        return sequence
    
    def generate_end_sequence(self) -> List[str]:
        """Генерация завершающей последовательности"""
        sequence = [
            "M104 S0 ; Turn off nozzle heater",
            "M140 S0 ; Turn off bed heater",
            "G28 X0 Y0 ; Home X and Y",
            "M84 ; Disable steppers",
        ]
        return sequence
    
    def generate_purge_line(self, length: float = 20) -> List[str]:
        """Генерация линии продувки"""
        sequence = [
            "G1 X5 Y5 Z0.2 F3000 ; Move to start",
            f"G1 X{5 + length} Y5 E{length * 0.5} F1500 ; Purge line",
        ]
        return sequence
    
    def optimize_commands(self, commands: List[GCodeCommand]) -> List[GCodeCommand]:
        """Оптимизация последовательности команд"""
        # Простая оптимизация: удаление дубликатов команд
        optimized = []
        last_command = None
        
        for cmd in commands:
            if cmd.command != last_command or cmd.parameters != last_command.parameters:
                optimized.append(cmd)
                last_command = cmd
        
        return optimized


gcode_generator = GCodeGenerator()

