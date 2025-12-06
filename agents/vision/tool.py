"""Vision Pipeline Tool для LangGraph"""
from typing import Dict, Any
from agents.vision.pipeline import vision_pipeline, VisionAnalysisResult


class VisionTool:
    """Инструмент для анализа изображений"""
    
    def analyze_image(self, image_path: str, use_claude: bool = False) -> Dict[str, Any]:
        """Полный анализ изображения печати"""
        result: VisionAnalysisResult = vision_pipeline.analyze_image(image_path, use_vlm=use_claude)
        
        return {
            "defects_detected": result.defects_detected,
            "severity": result.severity,
            "confidence": result.confidence,
            "recommendations": result.recommendations,
            "affected_region": result.affected_region,
            "vlm_analysis": result.vlm_analysis,
            "yolo_detections": result.yolo_detections,
            "defect_count": len(result.defects_detected),
            "has_defects": len(result.defects_detected) > 0
        }
    
    def detect_defects(self, image_path: str) -> Dict[str, Any]:
        """Обнаружение дефектов на изображении"""
        result: VisionAnalysisResult = vision_pipeline.analyze_image(image_path, use_vlm=False)
        
        return {
            "defects_detected": result.defects_detected,
            "severity": result.severity,
            "confidence": result.confidence,
            "yolo_detections": result.yolo_detections,
            "defect_count": len(result.defects_detected)
        }
    
    def get_tool_description(self) -> str:
        """Описание инструмента для LLM"""
        return """Vision Pipeline Tool для анализа изображений:
        - analyze_image: Полный анализ изображения печати (YOLOv8 + Claude Vision опционально)
        - detect_defects: Быстрое обнаружение дефектов на изображении (только YOLOv8)
        """


vision_tool = VisionTool()
