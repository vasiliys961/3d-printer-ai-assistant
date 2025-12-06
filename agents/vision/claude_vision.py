"""Claude Vision для сложных случаев анализа"""
from anthropic import Anthropic
from typing import Dict, Optional
from config import settings
import base64


class ClaudeVisionAnalyzer:
    """Анализатор изображений через Claude Vision"""
    
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
    
    def analyze_image(self, image_path: str, prompt: str = None) -> Dict:
        """Анализ изображения через Claude Vision"""
        try:
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            default_prompt = """Проанализируй это изображение 3D-печати. Определи:
            1. Есть ли видимые дефекты (слоистость, смещение слоев, пузыри, нити)?
            2. Качество печати (1-10)
            3. Рекомендации по улучшению
            Ответь структурированно на русском языке."""
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt or default_prompt
                        }
                    ]
                }]
            )
            
            return {
                "analysis": message.content[0].text,
                "model": "claude-3-5-sonnet-20241022",
                "success": True
            }
        except Exception as e:
            return {
                "error": str(e),
                "success": False
            }


claude_vision = ClaudeVisionAnalyzer()

