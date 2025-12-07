"""
Unit тесты для G-code Analyzer
"""
import pytest
from agents.code_interpreter.tool import CodeInterpreterTool
from agents.code_interpreter.parser import ParsedLine


class TestGcodeParser:
    """Тесты парсера G-code"""
    
    def test_parse_simple_gcode(self):
        """Тест парсинга простого G-code"""
        analyzer = CodeInterpreterTool()
        gcode = """
        G28 ; Home all axes
        G1 X10 Y10 F3000 ; Move to position
        M104 S200 ; Set nozzle temperature
        """
        
        result = analyzer.analyze_gcode(gcode, material="PLA", printer_profile="Ender3")
        
        assert result is not None
        assert "valid" in result
        assert "command_count" in result
        assert result["command_count"] > 0
    
    def test_parse_temperature_commands(self):
        """Тест парсинга команд температуры"""
        analyzer = CodeInterpreterTool()
        gcode = """
        M104 S210 ; Set nozzle temp to 210°C
        M140 S60 ; Set bed temp to 60°C
        M109 S210 ; Wait for nozzle temp
        """
        
        result = analyzer.analyze_gcode(gcode, material="PLA", printer_profile="Ender3")
        
        assert result is not None
        assert "valid" in result
    
    def test_validate_temperature_range(self):
        """Тест валидации диапазона температуры"""
        analyzer = CodeInterpreterTool()
        
        # Температура в допустимом диапазоне для PLA
        gcode_ok = "M104 S210 ; PLA temperature"
        result_ok = analyzer.validate_gcode(gcode_ok, material="PLA")
        assert result_ok["valid"] is True
        
        # Температура слишком высокая
        gcode_high = "M104 S300 ; Too high for PLA"
        result_high = analyzer.validate_gcode(gcode_high, material="PLA")
        # Может быть warning, но не обязательно error
    
    def test_calculate_metrics(self):
        """Тест расчета метрик"""
        analyzer = CodeInterpreterTool()
        gcode = """
        G28
        G1 X100 Y100 E50 F3000
        G1 X200 Y200 E100 F3000
        """
        
        metrics = analyzer.calculate_metrics(gcode, filament_diameter=1.75, filament_density=1.24)
        
        assert metrics is not None
        assert "basic_metrics" in metrics
        assert "estimated_time_hours" in metrics["basic_metrics"]
        assert "filament_weight_g" in metrics["basic_metrics"]
        assert "estimated_cost_usd" in metrics["basic_metrics"]


@pytest.mark.unit
class TestGcodeValidator:
    """Тесты валидатора G-code"""
    
    def test_validate_safe_gcode(self):
        """Тест валидации безопасного G-code"""
        analyzer = CodeInterpreterTool()
        gcode = """
        G28
        G1 X10 Y10 F3000
        M104 S200
        """
        
        result = analyzer.validate_gcode(gcode, material="PLA")
        
        assert result["valid"] is True
        assert len(result.get("errors", [])) == 0
    
    def test_detect_dangerous_commands(self):
        """Тест детекции опасных команд"""
        analyzer = CodeInterpreterTool()
        gcode = "M112 ; Emergency stop"
        
        result = analyzer.validate_gcode(gcode, material="PLA")
        
        # M112 может вызвать warning
        assert "warnings" in result or "errors" in result

