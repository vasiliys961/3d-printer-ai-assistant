"""YOLOv8 Object Detection"""
from ultralytics import YOLO
from typing import List, Dict, Tuple
import cv2
import numpy as np
from pathlib import Path


class YOLODetector:
    """Детектор объектов на основе YOLOv8"""
    
    def __init__(self, model_path: str = None):
        if model_path and Path(model_path).exists():
            self.model = YOLO(model_path)
        else:
            # Используем предобученную модель
            self.model = YOLO("yolov8n.pt")
    
    def detect_defects(self, image_path: str) -> Dict:
        """Обнаружение дефектов на изображении печати"""
        results = self.model(image_path)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                xyxy = box.xyxy[0].cpu().numpy()
                
                detections.append({
                    "class": cls,
                    "confidence": conf,
                    "bbox": xyxy.tolist(),
                    "class_name": self.model.names[cls]
                })
        
        # Определяем наличие дефектов
        defect_classes = ["layer_shift", "warping", "stringing", "blobs"]
        has_defect = any(
            det["class_name"] in defect_classes or det["confidence"] > 0.7
            for det in detections
        )
        
        return {
            "has_defect": has_defect,
            "detections": detections,
            "defect_count": len([d for d in detections if d["confidence"] > 0.5])
        }
    
    def analyze_print_quality(self, image_path: str) -> Dict:
        """Анализ качества печати"""
        defect_result = self.detect_defects(image_path)
        
        # Дополнительный анализ изображения
        img = cv2.imread(image_path)
        if img is None:
            return {"error": "Не удалось загрузить изображение"}
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Анализ контраста (показатель качества слоев)
        contrast = gray.std()
        
        # Анализ краев (показатель четкости)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        quality_score = min(100, (contrast / 50) * 30 + edge_density * 70)
        
        return {
            **defect_result,
            "quality_score": float(quality_score),
            "contrast": float(contrast),
            "edge_density": float(edge_density)
        }


yolo_detector = YOLODetector()

