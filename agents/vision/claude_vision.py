"""Claude Vision для сложных случаев анализа"""
from typing import Dict, Optional
import sys
import os

# Добавляем корневую директорию в путь для импорта config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import settings
from orchestration.llm_factory import get_llm
from langchain_core.messages import HumanMessage
import base64
import io
from PIL import Image


class ClaudeVisionAnalyzer:
    """Анализатор изображений через Claude Vision"""
    
    def __init__(self):
        # Используем фабрику LLM для поддержки разных провайдеров
        self.llm = get_llm()
    
    def analyze_image(self, image_input, prompt: str = None) -> Dict:
        """Анализ изображения через Claude Vision (поддерживает разные провайдеры)"""
        try:
            # Загружаем изображение
            if isinstance(image_input, str):
                # Путь к файлу
                image = Image.open(image_input)
            elif isinstance(image_input, Image.Image):
                image = image_input
            else:
                raise ValueError(f"Неподдерживаемый тип изображения: {type(image_input)}")
            
            # Конвертируем в base64
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            image_data = base64.b64encode(buffered.getvalue()).decode("utf-8")
            
            default_prompt = """Проанализируй это изображение 3D-печати. Определи:
            1. Есть ли видимые дефекты (слоистость, смещение слоев, пузыри, нити)?
            2. Качество печати (1-10)
            3. Рекомендации по улучшению
            Ответь структурированно на русском языке."""
            
            # Используем LangChain для отправки сообщения с изображением
            # OpenRouter и OpenAI-совместимые API используют формат image_url
            message = HumanMessage(
                content=[
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt or default_prompt
                    }
                ]
            )
            
            response = self.llm.invoke([message])
            
            return {
                "analysis": response.content if hasattr(response, 'content') else str(response),
                "model": getattr(settings, 'llm_provider', 'anthropic'),
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }


claude_vision = ClaudeVisionAnalyzer()

