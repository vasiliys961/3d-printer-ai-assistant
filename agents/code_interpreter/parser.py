"""Детальный анализатор G-code.

Функции:
1. Парсинг G-code → AST
2. Валидация параметров (температура, скорость, flow)
3. Детекция аномалий (temperature ramps, sudden direction changes)
4. Генерация рекомендаций по улучшению
5. Вычисление метрик (время печати, масса, стоимость)
"""

import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum


class GcodeCommand(Enum):
    """G-code команды, которые нас интересуют"""
    G0_RAPID = "G0"      # Быстрое движение
    G1_LINEAR = "G1"     # Линейное движение с экструзией
    G2_ARC_CW = "G2"     # Дуга (по часовой)
    G3_ARC_CCW = "G3"    # Дуга (против часовой)
    M104_HOTEND = "M104" # Установка температуры сопла (без ожидания)
    M109_HOTEND_WAIT = "M109" # С ожиданием
    M140_BED = "M140"    # Температура стола (без ожидания)
    M190_BED_WAIT = "M190" # С ожиданием
    G28_HOME = "G28"     # Домирование
    G29_PROBE = "G29"    # Автовыравнивание (ABL)


@dataclass
class ParsedLine:
    """Распарсенная строка G-code"""
    line_number: int
    command: str
    params: Dict[str, float]  # X, Y, Z, F, E, S...
    comment: Optional[str] = None


@dataclass
class PrintMetrics:
    """Метрики печати"""
    estimated_time_hours: float
    filament_weight_g: float
    estimated_cost_usd: float
    layer_count: int
    total_moves: int


class GcodeParser:
    """Парсер G-code файлов"""
    
    def __init__(self):
        # Регулярные выражения для парсинга
        self.command_pattern = re.compile(r'([GM]\d+(?:\.\d+)?)')
        self.parameter_pattern = re.compile(r'([A-Z])(-?\d+\.?\d*)')
        self.comment_pattern = re.compile(r';.*$')
    
    def parse_file(self, file_path: str) -> List[ParsedLine]:
        """Парсинг G-code файла"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_gcode(content)
    
    def parse_gcode(self, content: str) -> List[ParsedLine]:
        """
        Парсинг G-code в структурированный формат.
        """
        lines = []
        for i, raw_line in enumerate(content.split("\n"), 1):
            # Удаляем комментарии
            if ";" in raw_line:
                command_part, comment = raw_line.split(";", 1)
                comment = comment.strip()
            else:
                command_part, comment = raw_line, None
            
            command_part = command_part.strip()
            if not command_part:
                continue
            
            # Парсим команду и параметры
            tokens = command_part.split()
            cmd = tokens[0]
            
            # Извлекаем параметры (X10.5, Y20, F3000 и т.д.)
            params = {}
            for token in tokens[1:]:
                if len(token) > 1 and token[0].isalpha():
                    try:
                        params[token[0]] = float(token[1:])
                    except ValueError:
                        pass
            
            lines.append(ParsedLine(
                line_number=i,
                command=cmd,
                params=params,
                comment=comment
            ))
        
        return lines
    
    def parse_content(self, content: str) -> List[ParsedLine]:
        """Алиас для обратной совместимости"""
        return self.parse_gcode(content)
    
    def parse_line(self, line: str, line_number: int) -> Optional[ParsedLine]:
        """Парсинг одной строки G-code (для обратной совместимости)"""
        result = self.parse_gcode(line)
        return result[0] if result else None


# Создаем глобальный экземпляр для обратной совместимости
gcode_parser = GcodeParser()

# Для обратной совместимости с старым кодом
GCodeCommand = ParsedLine  # Алиас
