"""Генерация рекомендаций по улучшению G-code"""
from typing import List, Dict
from agents.code_interpreter.parser import ParsedLine
from agents.code_interpreter.validator import GCodeValidator


class RecommendationGenerator:
    """Генератор рекомендаций по улучшению G-code"""
    
    def __init__(self):
        self.validator = GCodeValidator()
    
    def generate_recommendations(
        self,
        parsed_lines: List[ParsedLine],
        material: str = "PLA",
        printer_profile: str = "Ender3"
    ) -> List[Dict[str, str]]:
        """
        Генерация рекомендаций по улучшению G-code на основе анализа.
        """
        recommendations = []
        
        # Анализ температуры
        temp_recommendations = self._analyze_temperature(parsed_lines, material)
        recommendations.extend(temp_recommendations)
        
        # Анализ скорости
        speed_recommendations = self._analyze_speed(parsed_lines)
        recommendations.extend(speed_recommendations)
        
        # Анализ экструзии
        extrusion_recommendations = self._analyze_extrusion(parsed_lines)
        recommendations.extend(extrusion_recommendations)
        
        # Анализ retracts
        retract_recommendations = self._analyze_retracts(parsed_lines)
        recommendations.extend(retract_recommendations)
        
        # Анализ слоев
        layer_recommendations = self._analyze_layers(parsed_lines)
        recommendations.extend(layer_recommendations)
        
        # Анализ движения
        movement_recommendations = self._analyze_movements(parsed_lines)
        recommendations.extend(movement_recommendations)
        
        return recommendations
    
    def _analyze_temperature(
        self,
        parsed_lines: List[ParsedLine],
        material: str
    ) -> List[Dict[str, str]]:
        """Анализ температуры и рекомендации"""
        recommendations = []
        mat_profile = self.validator.material_profiles.get(material, {})
        
        temps = []
        for line in parsed_lines:
            if line.command in ["M104", "M109"]:
                temp = line.params.get("S")
                if temp:
                    temps.append((line.line_number, temp))
        
        if temps:
            avg_temp = sum(t[1] for t in temps) / len(temps)
            recommended_min = mat_profile.get("temp_min", 190)
            recommended_max = mat_profile.get("temp_max", 215)
            
            if avg_temp < recommended_min:
                recommendations.append({
                    "type": "temperature",
                    "priority": "medium",
                    "title": "Температура сопла слишком низкая",
                    "description": f"Средняя температура {avg_temp:.1f}°C ниже рекомендуемой для {material} ({recommended_min}°C)",
                    "recommendation": f"Увеличьте температуру сопла до {recommended_min}-{recommended_max}°C для лучшего качества печати"
                })
            elif avg_temp > recommended_max:
                recommendations.append({
                    "type": "temperature",
                    "priority": "high",
                    "title": "Температура сопла слишком высокая",
                    "description": f"Средняя температура {avg_temp:.1f}°C выше рекомендуемой для {material} ({recommended_max}°C)",
                    "recommendation": f"Снизьте температуру сопла до {recommended_min}-{recommended_max}°C для предотвращения деградации материала"
                })
        
        return recommendations
    
    def _analyze_speed(self, parsed_lines: List[ParsedLine]) -> List[Dict[str, str]]:
        """Анализ скорости и рекомендации"""
        recommendations = []
        speeds = []
        
        for line in parsed_lines:
            if line.command == "G1" and "F" in line.params:
                speed = line.params["F"]
                speeds.append(speed)
        
        if speeds:
            avg_speed = sum(speeds) / len(speeds)
            max_speed = max(speeds)
            
            # Рекомендации по скорости
            if avg_speed > 6000:  # > 100 мм/с
                recommendations.append({
                    "type": "speed",
                    "priority": "medium",
                    "title": "Высокая скорость печати",
                    "description": f"Средняя скорость {avg_speed:.0f} мм/мин ({avg_speed/60:.1f} мм/с) может привести к снижению качества",
                    "recommendation": "Рассмотрите снижение скорости до 3000-4500 мм/мин для лучшего качества, особенно для внешних периметров"
                })
            elif avg_speed < 1500:  # < 25 мм/с
                recommendations.append({
                    "type": "speed",
                    "priority": "low",
                    "title": "Низкая скорость печати",
                    "description": f"Средняя скорость {avg_speed:.0f} мм/мин может значительно увеличить время печати",
                    "recommendation": "Можно увеличить скорость до 3000-4500 мм/мин для ускорения печати без потери качества"
                })
            
            # Проверка на резкие изменения скорости
            if len(speeds) > 1:
                speed_changes = [abs(speeds[i] - speeds[i-1]) for i in range(1, len(speeds))]
                max_change = max(speed_changes) if speed_changes else 0
                if max_change > 2000:
                    recommendations.append({
                        "type": "speed",
                        "priority": "low",
                        "title": "Резкие изменения скорости",
                        "description": f"Обнаружены резкие изменения скорости (до {max_change:.0f} мм/мин)",
                        "recommendation": "Плавные изменения скорости улучшают качество печати. Используйте постепенные переходы"
                    })
        
        return recommendations
    
    def _analyze_extrusion(self, parsed_lines: List[ParsedLine]) -> List[Dict[str, str]]:
        """Анализ экструзии и рекомендации"""
        recommendations = []
        extrusion_values = []
        
        for line in parsed_lines:
            if line.command == "G1" and "E" in line.params:
                e = line.params["E"]
                if e > 0:  # Только положительная экструзия
                    extrusion_values.append(e)
        
        if extrusion_values:
            avg_extrusion = sum(extrusion_values) / len(extrusion_values)
            max_extrusion = max(extrusion_values)
            
            if max_extrusion > 50:
                recommendations.append({
                    "type": "extrusion",
                    "priority": "high",
                    "title": "Подозрительно большая экструзия",
                    "description": f"Обнаружены значения экструзии до {max_extrusion:.2f} мм, что может указывать на ошибку слайсера",
                    "recommendation": "Проверьте настройки слайсера: диаметр сопла, ширину линии, множитель экструзии"
                })
        
        return recommendations
    
    def _analyze_retracts(self, parsed_lines: List[ParsedLine]) -> List[Dict[str, str]]:
        """Анализ retracts и рекомендации"""
        recommendations = []
        retracts = []
        
        for line in parsed_lines:
            if line.command == "G1" and "E" in line.params:
                e = line.params["E"]
                if e < 0:  # Retract
                    retracts.append(abs(e))
        
        if retracts:
            avg_retract = sum(retracts) / len(retracts)
            max_retract = max(retracts)
            
            if avg_retract > 5:
                recommendations.append({
                    "type": "retract",
                    "priority": "medium",
                    "title": "Большой retract",
                    "description": f"Средний retract {avg_retract:.2f} мм может быть избыточным",
                    "recommendation": f"Для большинства принтеров достаточно retract 2-4 мм. Рассмотрите снижение до 3-4 мм"
                })
            elif avg_retract < 1 and len(retracts) > 10:
                recommendations.append({
                    "type": "retract",
                    "priority": "low",
                    "title": "Маленький retract",
                    "description": f"Средний retract {avg_retract:.2f} мм может быть недостаточным для предотвращения stringing",
                    "recommendation": "Увеличьте retract до 2-4 мм для лучшего контроля stringing"
                })
        
        return recommendations
    
    def _analyze_layers(self, parsed_lines: List[ParsedLine]) -> List[Dict[str, str]]:
        """Анализ слоев и рекомендации"""
        recommendations = []
        z_values = []
        
        for line in parsed_lines:
            if line.command == "G1" and "Z" in line.params:
                z = line.params["Z"]
                z_values.append(z)
        
        if z_values:
            unique_z = sorted(set(z_values))
            layer_heights = [unique_z[i] - unique_z[i-1] for i in range(1, len(unique_z)) if unique_z[i] - unique_z[i-1] > 0]
            
            if layer_heights:
                avg_layer_height = sum(layer_heights) / len(layer_heights)
                
                if avg_layer_height > 0.3:
                    recommendations.append({
                        "type": "layer",
                        "priority": "medium",
                        "title": "Большая высота слоя",
                        "description": f"Средняя высота слоя {avg_layer_height:.2f} мм может снизить качество детализации",
                        "recommendation": "Для лучшего качества используйте высоту слоя 0.1-0.2 мм. Для быстрой печати можно использовать 0.2-0.3 мм"
                    })
                elif avg_layer_height < 0.05:
                    recommendations.append({
                        "type": "layer",
                        "priority": "low",
                        "title": "Очень маленькая высота слоя",
                        "description": f"Высота слоя {avg_layer_height:.2f} мм значительно увеличит время печати",
                        "recommendation": "Для большинства моделей достаточно 0.1-0.2 мм. Очень тонкие слои нужны только для особо детализированных моделей"
                    })
        
        return recommendations
    
    def _analyze_movements(self, parsed_lines: List[ParsedLine]) -> List[Dict[str, str]]:
        """Анализ движений и рекомендации"""
        recommendations = []
        
        # Подсчет типов движений
        rapid_moves = sum(1 for l in parsed_lines if l.command == "G0")
        linear_moves = sum(1 for l in parsed_lines if l.command == "G1")
        total_moves = rapid_moves + linear_moves
        
        if total_moves > 0:
            rapid_ratio = rapid_moves / total_moves
            
            if rapid_ratio > 0.3:
                recommendations.append({
                    "type": "movement",
                    "priority": "low",
                    "title": "Много быстрых перемещений",
                    "description": f"{rapid_ratio*100:.1f}% движений - быстрые перемещения (G0)",
                    "recommendation": "Рассмотрите оптимизацию пути печати для уменьшения количества перемещений"
                })
        
        return recommendations


recommendation_generator = RecommendationGenerator()

