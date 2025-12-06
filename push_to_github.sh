#!/bin/bash

# Скрипт для загрузки проекта на GitHub
# Использование: ./push_to_github.sh YOUR_GITHUB_USERNAME

if [ -z "$1" ]; then
    echo "❌ Ошибка: Укажите ваш GitHub username"
    echo ""
    echo "Использование:"
    echo "  ./push_to_github.sh YOUR_GITHUB_USERNAME"
    echo ""
    echo "Пример:"
    echo "  ./push_to_github.sh maxmobiles"
    exit 1
fi

GITHUB_USERNAME=$1
REPO_NAME="3d-printer-ai-assistant"

echo "🚀 Загрузка проекта на GitHub..."
echo ""
echo "GitHub username: $GITHUB_USERNAME"
echo "Repository name: $REPO_NAME"
echo ""

# Проверяем, есть ли уже remote
if git remote get-url origin &>/dev/null; then
    echo "⚠️  Remote 'origin' уже существует"
    read -p "Удалить и создать заново? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git remote remove origin
    else
        echo "❌ Отменено"
        exit 1
    fi
fi

# Добавляем remote
echo "📡 Добавляю remote репозиторий..."
git remote add origin "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"

# Убеждаемся, что ветка называется main
echo "🌿 Проверяю ветку..."
git branch -M main

# Показываем статус
echo ""
echo "📊 Текущий статус:"
git status

echo ""
read -p "Загрузить код на GitHub? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Отменено"
    exit 1
fi

# Загружаем на GitHub
echo "⬆️  Загружаю код на GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Успешно загружено на GitHub!"
    echo ""
    echo "🔗 Репозиторий: https://github.com/$GITHUB_USERNAME/$REPO_NAME"
else
    echo ""
    echo "❌ Ошибка при загрузке"
    echo ""
    echo "Возможные причины:"
    echo "  1. Репозиторий еще не создан на GitHub"
    echo "  2. Проблемы с аутентификацией"
    echo "  3. Неправильный username"
    echo ""
    echo "Создайте репозиторий на: https://github.com/new"
    exit 1
fi

