"""Компьютерное зрение для детекции дефектов 3D-печати.

Пайплайн:
1. Загрузка изображения (JPEG, PNG, HEIF)
2. Предпроцессинг (resize, normalize)
3. Локальная детекция (YOLOv8 - Spaghetti, warping, layer shift)
4. VLM анализ (Claude Vision - сложные случаи)
5. Генерация диагноза + рекомендаций
"""

import io
import base64
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import numpy as np
from PIL import Image
from dataclasses import dataclass

from agents.vision.yolo_detector import yolo_detector
from agents.vision.claude_vision import claude_vision
from config import settings


@dataclass
class VisionAnalysisResult:
    """Результат визуального анализа"""
    defects_detected: List[str]
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    recommendations: List[str]
    affected_region: Optional[Tuple[int, int, int, int]]  # (x1, y1, x2, y2)
    vlm_analysis: Optional[str]
    yolo_detections: List[Dict]


class VisionPipeline:
    """Пайплайн компьютерного зрения"""
    
    def __init__(self):
        """Инициализация моделей"""
        self.yolo_detector = yolo_detector
        self.claude_vision = claude_vision
    
    def analyze_image(self, image_input, use_vlm: bool = False) -> VisionAnalysisResult:
        """
        Главный метод анализа.
        
        Args:
            image_input: Path, bytes, PIL.Image или base64 string
            use_vlm: Использовать ли Claude Vision для детального анализа
        """
        # 1. Загрузка и нормализация
        image = self._load_image(image_input)
        
        # 2. Предпроцессинг
        processed_image = self._preprocess(image)
        
        # 3. Локальная детекция (YOLOv8)
        local_detections = self._detect_local(processed_image)
        
        # 4. VLM анализ (Claude Vision) - если есть дефекты или запрошен
        vlm_result = None
        if use_vlm or (local_detections and len(local_detections) > 0):
            vlm_result = self._analyze_vlm(processed_image)
        
        # 5. Синтез результатов
        all_defects = [d.get("class_name", d.get("class", "unknown")) for d in local_detections]
        if vlm_result:
            vlm_defects = self._extract_defects_from_vlm(vlm_result.get("analysis", ""))
            all_defects.extend(vlm_defects)
        
        # Убираем дубликаты
        all_defects = list(set(all_defects))
        
        severity = self._assess_severity(all_defects)
        recommendations = self._generate_recommendations(all_defects)
        confidence = self._calculate_confidence(local_detections)
        affected_region = self._find_region(local_detections)
        
        return VisionAnalysisResult(
            defects_detected=all_defects,
            severity=severity,
            confidence=confidence,
            recommendations=recommendations,
            affected_region=affected_region,
            vlm_analysis=vlm_result.get("analysis") if vlm_result else None,
            yolo_detections=local_detections
        )
    
    def _load_image(self, image_input) -> Image.Image:
        """Загрузка изображения из разных источников"""
        if isinstance(image_input, str):
            if image_input.startswith("data:"):
                # Base64
                b64_data = image_input.split(",")[1]
                image_data = base64.b64decode(b64_data)
                return Image.open(io.BytesIO(image_data))
            else:
                # Путь к файлу
                return Image.open(image_input)
        elif isinstance(image_input, bytes):
            return Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            return image_input
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")
    
    def _preprocess(self, image: Image.Image) -> Image.Image:
        """Предпроцессинг изображения"""
        # Resize если слишком большое (макс 1920x1920)
        max_size = 1920
        if image.width > max_size or image.height > max_size:
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Конвертируем в RGB если нужно
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        return image
    
    def _detect_local(self, image: Image.Image) -> List[Dict]:
        """Детекция дефектов через YOLOv8"""
        # Сохраняем временно для анализа
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            image.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            result = yolo_detector.analyze_print_quality(tmp_path)
            detections = []
            
            if result.get("detections"):
                for det in result["detections"]:
                    if det.get("confidence", 0) > 0.5:  # Filter low confidence
                        detections.append({
                            "class": det.get("class_name", "unknown"),
                            "class_name": det.get("class_name", "unknown"),
                            "confidence": det.get("confidence", 0.0),
                            "bbox": det.get("bbox", [0, 0, 0, 0])
                        })
            
            return detections
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _analyze_vlm(self, image: Image.Image) -> Dict:
        """Анализ через Claude Vision (VLM)"""
        # Сохраняем временно для анализа
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            image.save(tmp.name, 'JPEG')
            tmp_path = tmp.name
        
        try:
            result = claude_vision.analyze_image(tmp_path)
            return result
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def _extract_defects_from_vlm(self, vlm_text: str) -> List[str]:
        """Извлечение названий дефектов из VLM анализа"""
        defect_keywords = {
            "spaghetti": "spaghetti",
            "warping": "warping",
            "shift": "layer_shift",
            "stringing": "stringing",
            "under-extrusion": "under_extrusion",
            "over-extrusion": "over_extrusion",
            "blobs": "blobs",
            "zits": "zits",
            "layer lines": "layer_lines"
        }
        
        found = []
        vlm_lower = vlm_text.lower()
        
        for keyword, defect_name in defect_keywords.items():
            if keyword.lower() in vlm_lower:
                found.append(defect_name)
        
        return found
    
    def _assess_severity(self, defects: List[str]) -> str:
        """Оценка серьезности дефектов"""
        critical_defects = {"spaghetti", "layer_shift", "layer shift"}
        high_defects = {"warping", "stringing", "over_extrusion"}
        medium_defects = {"under_extrusion", "blobs", "zits"}
        
        defects_lower = [d.lower() for d in defects]
        
        if any(d in critical_defects for d in defects_lower):
            return "CRITICAL"
        elif any(d in high_defects for d in defects_lower):
            return "HIGH"
        elif any(d in medium_defects for d in defects_lower):
            return "MEDIUM"
        elif defects:
            return "LOW"
        else:
            return "LOW"
    
    def _generate_recommendations(self, defects: List[str]) -> List[str]:
        """Генерация рекомендаций на основе дефектов"""
        recommendations_map = {
            "spaghetti": [
                "Проверьте выравнивание стола (Z-offset)",
                "Убедитесь в адгезии первого слоя",
                "Очистите поверхность стола",
                "Проверьте температуру сопла и стола"
            ],
            "warping": [
                "Увеличьте температуру стола на 5-10°C",
                "Используйте brim или skirt для лучшей адгезии",
                "Добавьте корпус (enclosure) если возможно",
                "Проверьте температуру в помещении"
            ],
            "layer_shift": [
                "Проверьте натяжение ремней",
                "Проверьте соединения шаговых двигателей",
                "Снизьте скорость печати на 20%",
                "Проверьте механику принтера"
            ],
            "stringing": [
                "Увеличьте retract distance",
                "Увеличьте retract speed",
                "Снизьте температуру сопла на 5-10°C",
                "Включите Z-hop"
            ],
            "under_extrusion": [
                "Проверьте засорение сопла",
                "Увеличьте температуру сопла",
                "Проверьте настройки экструдера",
                "Проверьте диаметр филамента"
            ],
            "over_extrusion": [
                "Снизьте множитель экструзии",
                "Проверьте калибровку экструдера",
                "Снизьте температуру сопла"
            ],
            "blobs": [
                "Проверьте retract настройки",
                "Снизьте температуру сопла",
                "Проверьте скорость печати"
            ]
        }
        
        all_recs = []
        defects_lower = [d.lower() for d in defects]
        
        for defect in defects_lower:
            if defect in recommendations_map:
                all_recs.extend(recommendations_map[defect])
        
        # Если нет специфичных рекомендаций, даем общие
        if not all_recs:
            all_recs = [
                "Проверьте настройки слайсера",
                "Проверьте калибровку принтера",
                "Убедитесь в правильной температуре материала"
            ]
        
        return list(set(all_recs))[:5]  # Top 5 unique recommendations
    
    def _calculate_confidence(self, detections: List[Dict]) -> float:
        """Средняя уверенность модели"""
        if not detections:
            return 0.0
        
        scores = [d.get("confidence", 0.0) for d in detections]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _find_region(self, detections: List[Dict]) -> Optional[Tuple]:
        """Находит область с наибольшей плотностью дефектов"""
        if not detections:
            return None
        
        # Берем первый дефект как регион (можно улучшить для множественных дефектов)
        bbox = detections[0].get("bbox", [0, 0, 0, 0])
        if isinstance(bbox, list) and len(bbox) == 4:
            return tuple(bbox)
        return None


# Создаем глобальный экземпляр
vision_pipeline = VisionPipeline()

