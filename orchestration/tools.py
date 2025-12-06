"""Экспорт всех инструментов как LangChain StructuredTool"""
from langchain_core.tools import StructuredTool
from typing import Dict, Any
import json

from agents.code_interpreter.tool import code_interpreter_tool
from agents.rag_engine.tool import rag_engine_tool
from agents.vision.tool import vision_tool
from agents.hardware.tool import hardware_tool


# G-code Analyzer Tool
def analyze_gcode(gcode_content: str, material: str = "PLA", printer_profile: str = "Ender3") -> str:
    """Анализирует G-code файл и возвращает статистику, проблемы, аномалии и метрики"""
    result = code_interpreter_tool.analyze_gcode(gcode_content, material, printer_profile)
    return json.dumps(result, ensure_ascii=False, indent=2)


def validate_gcode(gcode_content: str, material: str = "PLA", printer_profile: str = "Ender3") -> str:
    """Валидирует G-code на безопасность"""
    result = code_interpreter_tool.validate_gcode(gcode_content, material, printer_profile)
    return json.dumps(result, ensure_ascii=False, indent=2)


def calculate_metrics(
    gcode_content: str,
    filament_diameter: float = 1.75,
    filament_density: float = 1.24,
    cost_per_gram: float = 0.02
) -> str:
    """Рассчитывает метрики печати: время, вес филамента, стоимость"""
    result = code_interpreter_tool.calculate_metrics(
        gcode_content, filament_diameter, filament_density, cost_per_gram
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


def detect_anomalies(gcode_content: str) -> str:
    """Обнаруживает аномалии в G-code (резкие изменения температуры, направления)"""
    result = code_interpreter_tool.detect_anomalies(gcode_content)
    return json.dumps(result, ensure_ascii=False, indent=2)


def get_recommendations(gcode_content: str, material: str = "PLA", printer_profile: str = "Ender3") -> str:
    """Генерирует рекомендации по улучшению G-code на основе анализа"""
    result = code_interpreter_tool.get_recommendations(gcode_content, material, printer_profile)
    return json.dumps(result, ensure_ascii=False, indent=2)


def generate_start_sequence(bed_temp: float = 60, nozzle_temp: float = 200) -> str:
    """Генерирует стартовую последовательность G-code"""
    return code_interpreter_tool.generate_start_sequence(bed_temp, nozzle_temp)


def generate_end_sequence() -> str:
    """Генерирует завершающую последовательность G-code"""
    return code_interpreter_tool.generate_end_sequence()


# RAG Engine Tool
async def search_knowledge(query: str, top_k: int = 5) -> str:
    """Ищет информацию в базе знаний по запросу (семантический поиск + BM25 re-ranking)"""
    result = await rag_engine_tool.search(query, top_k)
    return json.dumps(result, ensure_ascii=False, indent=2)


# Vision Pipeline Tool
def analyze_image(image_path: str, use_claude: bool = False) -> str:
    """Анализирует изображение печати на дефекты"""
    result = vision_tool.analyze_image(image_path, use_claude)
    return json.dumps(result, ensure_ascii=False, indent=2)


def detect_defects(image_path: str) -> str:
    """Обнаруживает дефекты на изображении печати"""
    result = vision_tool.detect_defects(image_path)
    return json.dumps(result, ensure_ascii=False, indent=2)


# Hardware Interface Tool
async def get_printer_status() -> str:
    """Получает текущий статус принтера"""
    result = await hardware_tool.get_status()
    return json.dumps(result, ensure_ascii=False, indent=2, default=str)


async def get_temperature() -> str:
    """Получает текущие температуры стола и сопла"""
    result = await hardware_tool.get_temperature()
    return json.dumps(result, ensure_ascii=False, indent=2)


async def set_temperature(bed_temp: float = None, nozzle_temp: float = None) -> str:
    """Устанавливает температуру стола и/или сопла"""
    result = await hardware_tool.set_temperature(bed_temp, nozzle_temp)
    return json.dumps({"success": result}, ensure_ascii=False)


async def start_print(gcode_file: str) -> str:
    """Начинает печать указанного G-code файла"""
    result = await hardware_tool.start_print(gcode_file)
    return json.dumps({"success": result}, ensure_ascii=False)


async def stop_print() -> str:
    """Останавливает текущую печать"""
    result = await hardware_tool.stop_print()
    return json.dumps({"success": result}, ensure_ascii=False)


async def pause_print() -> str:
    """Приостанавливает текущую печать"""
    result = await hardware_tool.pause_print()
    return json.dumps({"success": result}, ensure_ascii=False)


async def resume_print() -> str:
    """Возобновляет приостановленную печать"""
    result = await hardware_tool.resume_print()
    return json.dumps({"success": result}, ensure_ascii=False)


async def home_axes(axes: str = "XYZ") -> str:
    """Отправляет указанные оси в исходное положение"""
    result = await hardware_tool.home_axes(axes)
    return json.dumps({"success": result}, ensure_ascii=False)


# Создаем LangChain StructuredTool для каждого инструмента
# Каждый инструмент - это отдельный StructuredTool

# G-code инструменты
GcodeAnalyzer_analyze = StructuredTool.from_function(
    func=analyze_gcode,
    name="analyze_gcode",
    description="Детальный анализ G-code файла: валидация, аномалии, метрики, статистика"
)

GcodeAnalyzer_validate = StructuredTool.from_function(
    func=validate_gcode,
    name="validate_gcode",
    description="Валидирует G-code на безопасность с учетом материала и принтера"
)

GcodeAnalyzer_metrics = StructuredTool.from_function(
    func=calculate_metrics,
    name="calculate_metrics",
    description="Рассчитывает метрики печати: время, вес филамента, стоимость"
)

GcodeAnalyzer_anomalies = StructuredTool.from_function(
    func=detect_anomalies,
    name="detect_anomalies",
    description="Обнаруживает аномалии в G-code (резкие изменения температуры, направления)"
)

GcodeAnalyzer_recommendations = StructuredTool.from_function(
    func=get_recommendations,
    name="get_recommendations",
    description="Генерирует рекомендации по улучшению G-code на основе анализа (температура, скорость, экструзия, слои)"
)

GcodeAnalyzer_start = StructuredTool.from_function(
    func=generate_start_sequence,
    name="generate_start_sequence",
    description="Генерирует стартовую последовательность G-code"
)

GcodeAnalyzer_end = StructuredTool.from_function(
    func=generate_end_sequence,
    name="generate_end_sequence",
    description="Генерирует завершающую последовательность G-code"
)

# RAG инструменты
RAGEngine_search = StructuredTool.from_function(
    func=search_knowledge,
    name="search_knowledge",
    description="Ищет информацию в базе знаний о 3D-печати по запросу (семантический поиск + BM25 re-ranking)"
)

def ingest_knowledge_base(kb_path: str) -> str:
    """Загружает документы из директории в базу знаний"""
    result = rag_engine_tool.ingest_knowledge_base(kb_path)
    return json.dumps(result, ensure_ascii=False, indent=2)

RAGEngine_ingest = StructuredTool.from_function(
    func=ingest_knowledge_base,
    name="ingest_knowledge_base",
    description="Загружает документы (JSON, TXT, MD) из директории в базу знаний для последующего поиска"
)

# Vision инструменты
VisionPipeline_analyze = StructuredTool.from_function(
    func=analyze_image,
    name="analyze_image",
    description="Анализирует изображение печати на дефекты и качество"
)

VisionPipeline_detect = StructuredTool.from_function(
    func=detect_defects,
    name="detect_defects",
    description="Обнаруживает дефекты на изображении печати"
)

# Hardware инструменты
HardwareInterface_status = StructuredTool.from_function(
    func=get_printer_status,
    name="get_printer_status",
    description="Получает текущий статус принтера"
)

HardwareInterface_temperature = StructuredTool.from_function(
    func=get_temperature,
    name="get_temperature",
    description="Получает текущие температуры стола и сопла"
)

HardwareInterface_set_temp = StructuredTool.from_function(
    func=set_temperature,
    name="set_temperature",
    description="Устанавливает температуру стола и/или сопла"
)

HardwareInterface_start = StructuredTool.from_function(
    func=start_print,
    name="start_print",
    description="Начинает печать указанного G-code файла"
)

HardwareInterface_stop = StructuredTool.from_function(
    func=stop_print,
    name="stop_print",
    description="Останавливает текущую печать"
)

HardwareInterface_pause = StructuredTool.from_function(
    func=pause_print,
    name="pause_print",
    description="Приостанавливает текущую печать"
)

HardwareInterface_resume = StructuredTool.from_function(
    func=resume_print,
    name="resume_print",
    description="Возобновляет приостановленную печать"
)

HardwareInterface_home = StructuredTool.from_function(
    func=home_axes,
    name="home_axes",
    description="Отправляет указанные оси в исходное положение"
)

# Группируем инструменты по категориям для удобства
GcodeAnalyzer = [
    GcodeAnalyzer_analyze,
    GcodeAnalyzer_validate,
    GcodeAnalyzer_metrics,
    GcodeAnalyzer_anomalies,
    GcodeAnalyzer_recommendations,
    GcodeAnalyzer_start,
    GcodeAnalyzer_end,
]

RAGEngine = [RAGEngine_search, RAGEngine_ingest]

VisionPipeline = [
    VisionPipeline_analyze,
    VisionPipeline_detect,
]

HardwareInterface = [
    HardwareInterface_status,
    HardwareInterface_temperature,
    HardwareInterface_set_temp,
    HardwareInterface_start,
    HardwareInterface_stop,
    HardwareInterface_pause,
    HardwareInterface_resume,
    HardwareInterface_home,
]

