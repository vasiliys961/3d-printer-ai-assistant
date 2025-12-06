"""G-code Validator с детальной валидацией"""
from typing import List, Dict, Tuple
from agents.code_interpreter.parser import ParsedLine


class GCodeValidator:
    """Валидатор G-code команд с поддержкой профилей материалов"""
    
    def __init__(self):
        # Знания о материалах (будут загружены из KB)
        self.material_profiles = {
            "PLA": {"temp_min": 190, "temp_max": 215, "bed_temp": 50},
            "PETG": {"temp_min": 230, "temp_max": 250, "bed_temp": 70},
            "ABS": {"temp_min": 240, "temp_max": 260, "bed_temp": 100},
            "TPU": {"temp_min": 220, "temp_max": 240, "bed_temp": 50},
            "ASA": {"temp_min": 250, "temp_max": 270, "bed_temp": 100},
        }
        
        # Безопасные диапазоны параметров
        self.safe_ranges = {
            'E': (0, 1000),  # Экструдер
            'F': (1, 10000),  # Скорость подачи
            'X': (-500, 500),  # Оси
            'Y': (-500, 500),
            'Z': (0, 500),
            'S': (0, 300),  # Температура
        }
        
        # Опасные команды
        self.dangerous_commands = ['M112', 'M410']  # Emergency stop, quick stop
    
    def validate(
        self, 
        parsed_lines: List[ParsedLine], 
        printer_profile: str = "Ender3",
        material: str = "PLA"
    ) -> Dict:
        """
        Валидация G-code на предмет опасных параметров.
        """
        warnings = []
        errors = []
        
        # Получаем профиль материала
        mat_profile = self.material_profiles.get(material, self.material_profiles["PLA"])
        
        for line in parsed_lines:
            # Проверка температуры сопла
            if line.command in ["M104", "M109"]:
                temp = line.params.get("S")
                if temp:
                    temp_max = mat_profile.get("temp_max", 250)
                    temp_min = mat_profile.get("temp_min", 190)
                    if temp > temp_max + 20:
                        errors.append(
                            f"Line {line.line_number}: Temperature {temp}°C is dangerously high for {material} "
                            f"(max recommended: {temp_max}°C)"
                        )
                    elif temp < temp_min - 10:
                        warnings.append(
                            f"Line {line.line_number}: Temperature {temp}°C is low for {material} "
                            f"(min recommended: {temp_min}°C)"
                        )
            
            # Проверка температуры стола
            if line.command in ["M140", "M190"]:
                bed_temp = line.params.get("S")
                if bed_temp:
                    recommended_bed = mat_profile.get("bed_temp", 60)
                    if bed_temp > recommended_bed + 30:
                        warnings.append(
                            f"Line {line.line_number}: Bed temperature {bed_temp}°C is high "
                            f"(recommended: {recommended_bed}°C for {material})"
                        )
            
            # Проверка скорости
            if line.command == "G1":
                speed = line.params.get("F")  # мм/мин
                if speed and speed > 9000:  # > 150 мм/с
                    warnings.append(
                        f"Line {line.line_number}: High speed {speed} mm/min detected "
                        f"(>150 mm/s may cause quality issues)"
                    )
                elif speed and speed < 100:  # < 1.67 мм/с
                    warnings.append(
                        f"Line {line.line_number}: Very low speed {speed} mm/min detected"
                    )
            
            # Проверка E (экструзия)
            if line.command == "G1" and "E" in line.params:
                e = line.params["E"]
                # Чрезмерная экструзия может указывать на ошибку слайсера
                if e > 100:  # Вероятно, ошибка в G-code
                    errors.append(f"Line {line.line_number}: Suspicious E value: {e} (likely slicer error)")
                elif e < -10:  # Большой retract
                    warnings.append(f"Line {line.line_number}: Large retract: {e} mm")
            
            # Проверка опасных команд
            if line.command in self.dangerous_commands:
                warnings.append(f"Line {line.line_number}: Dangerous command {line.command} detected")
            
            # Проверка параметров на безопасные диапазоны
            for param, value in line.params.items():
                if param in self.safe_ranges:
                    min_val, max_val = self.safe_ranges[param]
                    if value < min_val or value > max_val:
                        errors.append(
                            f"Line {line.line_number}: Parameter {param}={value} "
                            f"out of safe range [{min_val}, {max_val}]"
                        )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "total_lines_analyzed": len(parsed_lines),
            "material": material,
            "printer_profile": printer_profile
        }
    
    def validate_temperature_sequence(self, commands: List[ParsedLine]) -> Tuple[bool, List[str]]:
        """Проверка последовательности температур"""
        issues = []
        has_heat = False
        has_cool = False
        last_temp = None
        
        for cmd in commands:
            if cmd.command in ["M104", "M109"]:
                temp = cmd.params.get("S")
                if temp:
                    if last_temp and abs(temp - last_temp) > 50:
                        issues.append(
                            f"Line {cmd.line_number}: Sudden temperature change "
                            f"from {last_temp}°C to {temp}°C"
                        )
                    last_temp = temp
                    has_heat = True
        
        return len(issues) == 0, issues
    
    def detect_anomalies(self, parsed_lines: List[ParsedLine]) -> Dict:
        """Детекция аномалий в G-code (temperature ramps, sudden direction changes)"""
        anomalies = []
        
        # Детекция резких изменений направления
        last_x, last_y, last_z = None, None, None
        last_direction = None
        
        for i, line in enumerate(parsed_lines):
            if line.command == "G1":
                x = line.params.get("X", last_x)
                y = line.params.get("Y", last_y)
                z = line.params.get("Z", last_z)
                
                if last_x is not None and last_y is not None and x is not None and y is not None:
                    # Вычисляем направление движения
                    dx = x - last_x
                    dy = y - last_y
                    
                    if dx != 0 or dy != 0:
                        # Нормализуем вектор направления
                        length = (dx*dx + dy*dy) ** 0.5
                        if length > 0:
                            direction = (dx/length, dy/length)
                            
                            # Проверяем резкое изменение направления
                            if last_direction is not None:
                                # Вычисляем угол между направлениями
                                dot_product = last_direction[0] * direction[0] + last_direction[1] * direction[1]
                                # Ограничиваем dot_product для избежания ошибок округления
                                dot_product = max(-1.0, min(1.0, dot_product))
                                angle_rad = __import__('math').acos(dot_product)
                                angle_deg = angle_rad * 180 / __import__('math').pi
                                
                                # Резкое изменение направления (> 135 градусов)
                                if angle_deg > 135:
                                    anomalies.append({
                                        "type": "sudden_direction_change",
                                        "line": line.line_number,
                                        "description": f"Sudden direction change detected (angle: {angle_deg:.1f}°)",
                                        "severity": "medium"
                                    })
                            
                            last_direction = direction
                
                if x is not None:
                    last_x = x
                if y is not None:
                    last_y = y
                if z is not None:
                    last_z = z
        
        # Детекция temperature ramps
        temp_changes = []
        for line in parsed_lines:
            if line.command in ["M104", "M109", "M140", "M190"]:
                temp = line.params.get("S")
                if temp is not None:
                    temp_changes.append((line.line_number, temp, line.command))
        
        if len(temp_changes) > 1:
            for i in range(1, len(temp_changes)):
                prev_line, prev_temp, prev_cmd = temp_changes[i-1]
                curr_line, curr_temp, curr_cmd = temp_changes[i]
                temp_diff = abs(curr_temp - prev_temp)
                
                # Резкое изменение температуры (> 30°C)
                if temp_diff > 30:
                    anomalies.append({
                        "type": "temperature_ramp",
                        "line": curr_line,
                        "description": f"Rapid temperature change from {prev_temp}°C to {curr_temp}°C (change: {temp_diff:.1f}°C)",
                        "severity": "high" if temp_diff > 50 else "medium",
                        "previous_command": prev_cmd,
                        "current_command": curr_cmd
                    })
        
        # Детекция подозрительных паттернов экструзии
        consecutive_extrusions = 0
        max_consecutive = 0
        for line in parsed_lines:
            if line.command == "G1" and "E" in line.params:
                e = line.params["E"]
                if e > 0:
                    consecutive_extrusions += 1
                    max_consecutive = max(max_consecutive, consecutive_extrusions)
                else:
                    consecutive_extrusions = 0
        
        if max_consecutive > 1000:
            anomalies.append({
                "type": "excessive_extrusion",
                "line": None,
                "description": f"Very long sequence of extrusion moves ({max_consecutive} consecutive)",
                "severity": "low"
            })
        
        return {
            "anomalies": anomalies,
            "anomaly_count": len(anomalies),
            "by_type": {
                "temperature_ramp": len([a for a in anomalies if a["type"] == "temperature_ramp"]),
                "sudden_direction_change": len([a for a in anomalies if a["type"] == "sudden_direction_change"]),
                "excessive_extrusion": len([a for a in anomalies if a["type"] == "excessive_extrusion"])
            }
        }
    
    def get_statistics(self, commands: List[ParsedLine]) -> Dict:
        """Получить статистику по G-code"""
        stats = {
            'total_commands': len(commands),
            'g_commands': sum(1 for c in commands if c.command.startswith('G')),
            'm_commands': sum(1 for c in commands if c.command.startswith('M')),
            'has_temperature': any('S' in c.params for c in commands if c.command.startswith('M')),
            'has_extrusion': any('E' in c.params for c in commands if c.command == 'G1'),
            'max_temperature': max(
                (c.params.get('S', 0) for c in commands if 'S' in c.params),
                default=0
            ),
            'min_temperature': min(
                (c.params.get('S', 300) for c in commands if 'S' in c.params),
                default=0
            ) if any('S' in c.params for c in commands) else 0,
        }
        return stats


gcode_validator = GCodeValidator()
