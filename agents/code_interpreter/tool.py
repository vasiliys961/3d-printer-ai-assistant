"""Code Interpreter Tool для LangGraph"""
from typing import Dict, Any
from agents.code_interpreter.parser import gcode_parser, ParsedLine
from agents.code_interpreter.validator import gcode_validator
from agents.code_interpreter.generator import gcode_generator
from agents.code_interpreter.metrics import metrics_calculator
from agents.code_interpreter.recommendations import recommendation_generator


class CodeInterpreterTool:
    """Инструмент для анализа и работы с G-code"""
    
    def analyze_gcode(
        self, 
        gcode_content: str,
        material: str = "PLA",
        printer_profile: str = "Ender3"
    ) -> Dict[str, Any]:
        """Детальный анализ G-code"""
        parsed_lines = gcode_parser.parse_gcode(gcode_content)
        
        # Валидация
        validation_result = gcode_validator.validate(parsed_lines, printer_profile, material)
        
        # Детекция аномалий
        anomalies = gcode_validator.detect_anomalies(parsed_lines)
        
        # Статистика
        stats = gcode_validator.get_statistics(parsed_lines)
        
        # Метрики
        metrics = metrics_calculator.estimate_metrics(parsed_lines)
        detailed_metrics = metrics_calculator.get_detailed_metrics(parsed_lines)
        
        # Рекомендации
        recommendations = recommendation_generator.generate_recommendations(
            parsed_lines, material, printer_profile
        )
        
        return {
            "valid": validation_result["valid"],
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"],
            "anomalies": anomalies["anomalies"],
            "anomaly_count": anomalies["anomaly_count"],
            "anomalies_by_type": anomalies.get("by_type", {}),
            "statistics": stats,
            "metrics": {
                "estimated_time_hours": metrics.estimated_time_hours,
                "estimated_time_minutes": metrics.estimated_time_hours * 60,
                "filament_weight_g": metrics.filament_weight_g,
                "estimated_cost_usd": metrics.estimated_cost_usd,
                "layer_count": metrics.layer_count,
                "total_moves": metrics.total_moves,
            },
            "detailed_metrics": detailed_metrics,
            "recommendations": recommendations,
            "recommendation_count": len(recommendations),
            "command_count": len(parsed_lines),
            "material": material,
            "printer_profile": printer_profile
        }
    
    def validate_gcode(
        self, 
        gcode_content: str,
        material: str = "PLA",
        printer_profile: str = "Ender3"
    ) -> Dict[str, Any]:
        """Валидация G-code на безопасность"""
        parsed_lines = gcode_parser.parse_gcode(gcode_content)
        validation_result = gcode_validator.validate(parsed_lines, printer_profile, material)
        temp_valid, temp_issues = gcode_validator.validate_temperature_sequence(parsed_lines)
        
        return {
            "valid": validation_result["valid"] and temp_valid,
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"] + temp_issues,
            "total_lines_analyzed": validation_result["total_lines_analyzed"],
            "material": material,
            "printer_profile": printer_profile
        }
    
    def calculate_metrics(
        self,
        gcode_content: str,
        filament_diameter: float = 1.75,
        filament_density: float = 1.24,
        cost_per_gram: float = 0.02
    ) -> Dict[str, Any]:
        """Расчет метрик печати"""
        parsed_lines = gcode_parser.parse_gcode(gcode_content)
        metrics = metrics_calculator.estimate_metrics(
            parsed_lines,
            filament_diameter,
            filament_density,
            cost_per_gram
        )
        detailed_metrics = metrics_calculator.get_detailed_metrics(
            parsed_lines,
            filament_diameter,
            filament_density
        )
        
        return {
            "basic_metrics": {
                "estimated_time_hours": metrics.estimated_time_hours,
                "estimated_time_minutes": metrics.estimated_time_hours * 60,
                "filament_weight_g": metrics.filament_weight_g,
                "estimated_cost_usd": metrics.estimated_cost_usd,
                "layer_count": metrics.layer_count,
                "total_moves": metrics.total_moves,
            },
            "detailed_metrics": detailed_metrics["advanced_metrics"],
            "filament_parameters": {
                "diameter_mm": filament_diameter,
                "density_g_cm3": filament_density,
                "cost_per_gram_usd": cost_per_gram
            }
        }
    
    def detect_anomalies(self, gcode_content: str) -> Dict[str, Any]:
        """Детекция аномалий в G-code"""
        parsed_lines = gcode_parser.parse_gcode(gcode_content)
        anomalies = gcode_validator.detect_anomalies(parsed_lines)
        
        return {
            "anomalies": anomalies["anomalies"],
            "anomaly_count": anomalies["anomaly_count"],
            "total_lines": len(parsed_lines)
        }
    
    def generate_start_sequence(self, bed_temp: float = 60, nozzle_temp: float = 200) -> str:
        """Генерация стартовой последовательности"""
        sequence = gcode_generator.generate_start_sequence(bed_temp, nozzle_temp)
        return "\n".join(sequence)
    
    def generate_end_sequence(self) -> str:
        """Генерация завершающей последовательности"""
        sequence = gcode_generator.generate_end_sequence()
        return "\n".join(sequence)
    
    def get_recommendations(
        self,
        gcode_content: str,
        material: str = "PLA",
        printer_profile: str = "Ender3"
    ) -> Dict[str, Any]:
        """Генерация рекомендаций по улучшению G-code"""
        parsed_lines = gcode_parser.parse_gcode(gcode_content)
        recommendations = recommendation_generator.generate_recommendations(
            parsed_lines, material, printer_profile
        )
        
        return {
            "recommendations": recommendations,
            "count": len(recommendations),
            "by_priority": {
                "high": len([r for r in recommendations if r.get("priority") == "high"]),
                "medium": len([r for r in recommendations if r.get("priority") == "medium"]),
                "low": len([r for r in recommendations if r.get("priority") == "low"])
            }
        }
    
    def get_tool_description(self) -> str:
        """Описание инструмента для LLM"""
        return """Code Interpreter Tool для работы с G-code:
        - analyze_gcode: Детальный анализ G-code файла (валидация, аномалии, метрики, рекомендации)
        - validate_gcode: Валидация G-code на безопасность
        - calculate_metrics: Расчет метрик печати (время, вес, стоимость)
        - detect_anomalies: Детекция аномалий в G-code
        - get_recommendations: Генерация рекомендаций по улучшению G-code
        - generate_start_sequence: Генерация стартовой последовательности
        - generate_end_sequence: Генерация завершающей последовательности
        """


code_interpreter_tool = CodeInterpreterTool()
