"""Расчет метрик печати"""
from typing import List
from agents.code_interpreter.parser import ParsedLine, PrintMetrics
import math


class MetricsCalculator:
    """Калькулятор метрик печати"""
    
    def estimate_metrics(
        self, 
        parsed_lines: List[ParsedLine],
        filament_diameter: float = 1.75,
        filament_density: float = 1.24,
        cost_per_gram: float = 0.02
    ) -> PrintMetrics:
        """
        Расчет метрик печати (время, вес, стоимость).
        """
        total_distance = 0.0
        total_e = 0.0
        speeds = []
        z_values = []
        last_x, last_y, last_z = None, None, None
        
        for line in parsed_lines:
            if line.command == "G1":
                # Линейное движение
                speed = line.params.get("F")
                if speed:
                    speeds.append(speed)
                
                # Извлекаем координаты
                x = line.params.get("X", last_x)
                y = line.params.get("Y", last_y)
                z = line.params.get("Z", last_z)
                
                # Вычисляем расстояние
                if last_x is not None and last_y is not None:
                    if x is not None and y is not None:
                        dx = x - last_x
                        dy = y - last_y
                        distance = math.sqrt(dx*dx + dy*dy)
                        total_distance += distance
                
                # Отслеживаем Z для подсчета слоев
                if z is not None:
                    z_values.append(z)
                
                # Суммируем экструзию
                if "E" in line.params:
                    e = line.params["E"]
                    if e > 0:  # Только положительная экструзия
                        total_e += e
                
                # Обновляем последние координаты
                if x is not None:
                    last_x = x
                if y is not None:
                    last_y = y
                if z is not None:
                    last_z = z
        
        # Расчеты
        avg_speed = sum(speeds) / len(speeds) if speeds else 3000  # мм/мин
        
        # Время печати (упрощенный расчет)
        # Учитываем только движения с экструзией
        time_hours = total_distance / (avg_speed * 60) if avg_speed > 0 else 0
        
        # Объем экструдированного материала
        # E значение обычно в мм, нужно перевести в объем
        # Предполагаем, что E - это длина экструдированного филамента
        volume_mm3 = (total_e / 1000) * math.pi * (filament_diameter / 2) ** 2
        volume_cm3 = volume_mm3 / 1000
        
        # Вес
        weight_g = volume_cm3 * filament_density
        
        # Стоимость
        cost_usd = weight_g * cost_per_gram
        
        # Подсчет слоев (по уникальным Z значениям)
        unique_z = sorted(set(z_values))
        layer_count = len(unique_z)
        
        # Общее количество движений
        total_moves = len([l for l in parsed_lines if l.command == "G1"])
        
        return PrintMetrics(
            estimated_time_hours=time_hours,
            filament_weight_g=weight_g,
            estimated_cost_usd=cost_usd,
            layer_count=layer_count,
            total_moves=total_moves
        )
    
    def get_detailed_metrics(
        self,
        parsed_lines: List[ParsedLine],
        filament_diameter: float = 1.75,
        filament_density: float = 1.24
    ) -> Dict:
        """Получить детальные метрики"""
        metrics = self.estimate_metrics(parsed_lines, filament_diameter, filament_density)
        
        # Дополнительные метрики
        retracts = sum(1 for l in parsed_lines if l.command == "G1" and l.params.get("E", 0) < 0)
        temperature_changes = sum(1 for l in parsed_lines if l.command in ["M104", "M109", "M140", "M190"])
        
        return {
            "basic_metrics": {
                "estimated_time_hours": metrics.estimated_time_hours,
                "estimated_time_minutes": metrics.estimated_time_hours * 60,
                "filament_weight_g": metrics.filament_weight_g,
                "filament_weight_kg": metrics.filament_weight_g / 1000,
                "estimated_cost_usd": metrics.estimated_cost_usd,
                "layer_count": metrics.layer_count,
                "total_moves": metrics.total_moves,
            },
            "advanced_metrics": {
                "retract_count": retracts,
                "temperature_changes": temperature_changes,
                "filament_length_m": metrics.filament_weight_g / (filament_density * math.pi * (filament_diameter/2)**2 * 1000),
            }
        }


metrics_calculator = MetricsCalculator()

