"""
Тестовый скрипт для проверки работоспособности MultiModelAgent
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.multi_model_agent import MultiModelAgent, AnalyzerOutput, ConsultantOutput


async def test_analyzer():
    """Тест Аналитика"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Аналитик")
    print("="*60)
    
    agent = MultiModelAgent()
    user_message = "Почему мой первый слой не прилипает к столу? Использую PLA на 200°C."
    
    print(f"Запрос: {user_message}\n")
    
    try:
        analyzer_output = await agent.call_analyzer(user_message)
        print(f"✅ Аналитик отработал успешно")
        print(f"\nЦель: {analyzer_output.goal}")
        print(f"Подзадач: {len(analyzer_output.subtasks)}")
        print(f"Ключевых слов: {len(analyzer_output.keywords)}")
        print(f"В домене: {analyzer_output.domain_check}")
        if analyzer_output.subtasks:
            print(f"\nПервые 3 подзадачи:")
            for i, task in enumerate(analyzer_output.subtasks[:3], 1):
                print(f"  {i}. {task}")
        if analyzer_output.keywords:
            print(f"\nКлючевые слова: {', '.join(analyzer_output.keywords[:5])}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_consultant():
    """Тест Консультанта"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Консультант")
    print("="*60)
    
    agent = MultiModelAgent()
    user_message = "Как настроить температуру для PETG?"
    
    # Создаем тестовый вывод Аналитика
    analyzer_output = AnalyzerOutput(
        goal="Настройка температуры для PETG",
        subtasks=["Определить оптимальную температуру сопла", "Определить температуру стола"],
        keywords=["PETG", "температура", "настройка"],
        critical_data={"materials": ["PETG"]},
        domain_check=True,
        missing_info=[]
    )
    
    rag_context = "PETG: 230-250°C сопло, 70-80°C стол. Не требует активного охлаждения."
    
    print(f"Запрос: {user_message}\n")
    print(f"Контекст RAG: {rag_context}\n")
    
    try:
        consultant_output = await agent.call_consultant(user_message, analyzer_output, rag_context)
        print(f"✅ Консультант отработал успешно")
        print(f"\nКраткий вывод:\n{consultant_output.brief_summary[:200]}...")
        print(f"\nТехнических пунктов: {len(consultant_output.technical_breakdown)}")
        print(f"Рекомендуемых действий: {len(consultant_output.recommended_actions)}")
        if consultant_output.technical_breakdown:
            print(f"\nПервый пункт технического разбора:")
            print(f"  {consultant_output.technical_breakdown[0][:150]}...")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_pipeline():
    """Тест полного пайплайна"""
    print("\n" + "="*60)
    print("ТЕСТ 3: Полный пайплайн (без БД)")
    print("="*60)
    
    agent = MultiModelAgent()
    user_message = "Почему мой пластик в воздухе висит при печати?"
    
    print(f"Запрос: {user_message}\n")
    
    try:
        # Запускаем без БД (session_id=None, db=None)
        response = await agent.run(user_message, session_id=None, db=None)
        print(f"✅ Полный пайплайн отработал успешно")
        print(f"\nДлина ответа: {len(response)} символов")
        print(f"\nПервые 500 символов ответа:")
        print("-" * 60)
        print(response[:500])
        print("-" * 60)
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_qa_checker():
    """Тест Проверяющего"""
    print("\n" + "="*60)
    print("ТЕСТ 4: Проверяющий (QA Checker)")
    print("="*60)
    
    agent = MultiModelAgent()
    
    # Создаем тестовый вывод Консультанта
    consultant_output = ConsultantOutput(
        brief_summary="Проблема с адгезией первого слоя может быть вызвана неправильной температурой стола или загрязнением поверхности.",
        technical_breakdown=[
            "Температура стола для PLA должна быть 50-60°C",
            "Поверхность стола должна быть чистой и ровной"
        ],
        recommended_actions=[
            "Проверить температуру стола",
            "Очистить поверхность стола",
            "Проверить уровень стола"
        ],
        what_to_clarify=["Текущая температура стола", "Тип поверхности стола"]
    )
    
    print("Тестирую оценку качества ответа Консультанта...\n")
    
    try:
        qa_output = await agent.call_qa_checker(consultant_output)
        print(f"✅ Проверяющий отработал успешно")
        print(f"\nОценки:")
        print(f"  Корректность: {qa_output.correctness}/10")
        print(f"  Полнота: {qa_output.completeness}/10")
        print(f"  Ясность: {qa_output.clarity}/10")
        if qa_output.comments:
            print(f"\nКомментарии:")
            if qa_output.comments.get("strengths"):
                print(f"  Сильные стороны: {len(qa_output.comments['strengths'])}")
            if qa_output.comments.get("issues"):
                print(f"  Проблемы: {len(qa_output.comments['issues'])}")
            if qa_output.comments.get("risksOrHallucinations"):
                print(f"  Риски/галлюцинации: {len(qa_output.comments['risksOrHallucinations'])}")
        return True
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Главная функция тестирования"""
    print("\n" + "="*60)
    print("ТЕСТИРОВАНИЕ МУЛЬТИАГЕНТНОЙ СИСТЕМЫ")
    print("="*60)
    
    results = []
    
    # Тест 1: Аналитик
    results.append(await test_analyzer())
    
    # Тест 2: Консультант
    results.append(await test_consultant())
    
    # Тест 3: Полный пайплайн
    results.append(await test_full_pipeline())
    
    # Тест 4: Проверяющий
    results.append(await test_qa_checker())
    
    # Итоги
    print("\n" + "="*60)
    print("ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    print(f"Успешно: {sum(results)}/{len(results)}")
    print(f"Провалено: {len(results) - sum(results)}/{len(results)}")
    
    if all(results):
        print("\n✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
    else:
        print("\n⚠️ Некоторые тесты провалены")
    
    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

