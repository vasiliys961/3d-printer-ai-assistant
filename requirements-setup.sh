#!/bin/bash
# Скрипт для установки зависимостей с учетом Python 3.13

echo "Установка зависимостей для 3D Printer AI Assistant..."

# Активируем виртуальное окружение если оно существует
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Обновляем pip
pip install --upgrade pip setuptools wheel

# Устанавливаем torch и torchvision через PyTorch index (для Python 3.13)
echo "Установка PyTorch..."
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Устанавливаем остальные зависимости
echo "Установка остальных зависимостей..."
pip install -r requirements.txt

echo "Готово! Все зависимости установлены."

