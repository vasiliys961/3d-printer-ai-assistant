"""
Скрипт для добавления source_url во все документы базы знаний
"""
import json
import os
from pathlib import Path


# Маппинг категорий на базовые URL 3Dtoday.ru
CATEGORY_URLS = {
    "materials": "https://3dtoday.ru/wiki/materials/",
    "troubleshooting": "https://3dtoday.ru/wiki/troubleshooting/",
    "printer_profiles": "https://3dtoday.ru/wiki/printers/",
    "gcode_commands": "https://3dtoday.ru/wiki/gcode/",
    "calibration": "https://3dtoday.ru/wiki/calibration/",
    "slicer_settings": "https://3dtoday.ru/wiki/slicers/"
}


def add_source_url_to_file(file_path: Path):
    """Добавить source_url в JSON файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Определяем категорию из пути
        category = None
        for cat in CATEGORY_URLS.keys():
            if cat in str(file_path):
                category = cat
                break
        
        if not category:
            # Пытаемся определить из содержимого
            if isinstance(data, list) and len(data) > 0:
                category = data[0].get("category")
        
        base_url = CATEGORY_URLS.get(category, "https://3dtoday.ru/wiki/")
        
        # Генерируем URL на основе имени файла
        file_name = file_path.stem
        source_url = f"{base_url}{file_name}/"
        
        modified = False
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict) and "source_url" not in item:
                    item["source_url"] = source_url
                    modified = True
        elif isinstance(data, dict):
            if "source_url" not in data:
                data["source_url"] = source_url
                modified = True
        
        if modified:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        
        return False
    
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {e}")
        return False


def main():
    """Основная функция"""
    kb_path = Path("./data/knowledge_base")
    
    if not kb_path.exists():
        print(f"❌ Директория {kb_path} не найдена")
        return
    
    print(f"📚 Добавление source_url в документы базы знаний...")
    print(f"📂 Путь: {kb_path}")
    
    json_files = list(kb_path.rglob("*.json"))
    modified_count = 0
    
    for json_file in json_files:
        if add_source_url_to_file(json_file):
            modified_count += 1
            print(f"✅ Обновлен: {json_file.relative_to(kb_path)}")
    
    print(f"\n✅ Готово! Обновлено файлов: {modified_count}/{len(json_files)}")
    print(f"💡 Примечание: source_url содержат placeholder ссылки на 3dtoday.ru")
    print(f"   Замените их на реальные ссылки при необходимости")


if __name__ == "__main__":
    main()

