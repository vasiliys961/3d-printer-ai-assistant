"""База данных проектов"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Project:
    """Проект для печати"""
    id: str
    name: str
    description: str
    difficulty: str  # easy, medium, hard
    estimated_time_hours: int
    required_material: str
    required_skills: List[str] = field(default_factory=list)
    stl_url: str = ""
    instructions: str = ""
    image_url: str = ""


PROJECTS = [
    Project(
        id="project_001",
        name="Калибровочный куб",
        description="Простой куб 20×20×20 мм для калибровки принтера",
        difficulty="easy",
        estimated_time_hours=1,
        required_material="PLA",
        required_skills=["bed_leveling"],
        instructions="Напечатайте куб и проверьте размеры штангенциркулем"
    ),
    Project(
        id="project_002",
        name="Тест на stringing",
        description="Две башни для тестирования retraction настроек",
        difficulty="easy",
        estimated_time_hours=1,
        required_material="PLA",
        required_skills=["retraction"],
        instructions="Напечатайте тест и проверьте наличие нитей между башнями"
    ),
    Project(
        id="project_003",
        name="Temperature Tower",
        description="Башня для определения оптимальной температуры материала",
        difficulty="medium",
        estimated_time_hours=2,
        required_material="PLA",
        required_skills=["temperature", "slicer_settings"],
        instructions="Настройте изменение температуры по слоям в слайсере"
    ),
    Project(
        id="project_004",
        name="Органайзер для инструментов",
        description="Практичный органайзер для хранения инструментов",
        difficulty="medium",
        estimated_time_hours=4,
        required_material="PLA",
        required_skills=["bed_leveling", "supports"],
        instructions="Используйте поддержки для нависающих элементов"
    ),
    Project(
        id="project_005",
        name="Корпус для электроники",
        description="Корпус для Arduino/Raspberry Pi с точными размерами",
        difficulty="hard",
        estimated_time_hours=6,
        required_material="PETG",
        required_skills=["precision", "supports", "post_processing"],
        instructions="Требуется точная калибровка и возможно постобработка"
    )
]

