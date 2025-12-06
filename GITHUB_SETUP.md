# Инструкция по загрузке на GitHub

## Шаг 1: Создание репозитория на GitHub

1. Перейдите на https://github.com/new
2. Заполните форму:
   - **Repository name:** `3d-printer-ai-assistant`
   - **Description:** `Интеллектуальный помощник по 3D-печати с мультиагентной архитектурой на LangGraph`
   - **Visibility:** Public или Private (на ваш выбор)
   - **НЕ создавайте:** README, .gitignore, license (у нас уже есть)

3. Нажмите "Create repository"

## Шаг 2: Подключение к GitHub

После создания репозитория выполните следующие команды:

```bash
# Добавить remote репозиторий (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/3d-printer-ai-assistant.git

# Убедиться, что ветка называется main
git branch -M main

# Загрузить код на GitHub
git push -u origin main
```

## Шаг 3: Проверка

После загрузки проверьте:
- https://github.com/YOUR_USERNAME/3d-printer-ai-assistant
- README.md отображается корректно
- Все файлы загружены

## Дополнительные настройки (опционально)

### Добавить описание репозитория
В настройках репозитория добавьте:
- Topics: `3d-printing`, `ai`, `langgraph`, `fastapi`, `python`, `claude-ai`
- Website: (если есть)
- Description: `Интеллектуальный помощник по 3D-печати с мультиагентной архитектурой`

### Настроить GitHub Actions (если нужно)
Создайте `.github/workflows/ci.yml` для автоматических тестов.

### Добавить лицензию
Если хотите, добавьте файл `LICENSE` (MIT, Apache 2.0 и т.д.)

## Проблемы?

Если возникли проблемы:

1. **Ошибка "remote origin already exists":**
   ```bash
   git remote remove origin
   git remote add origin https://github.com/YOUR_USERNAME/3d-printer-ai-assistant.git
   ```

2. **Ошибка аутентификации:**
   - Используйте Personal Access Token вместо пароля
   - Или настройте SSH ключи

3. **Большие файлы:**
   - Убедитесь, что `.gitignore` правильно настроен
   - Модели YOLOv8 должны быть в `.gitignore`

