#!/usr/bin/env python3
"""
Менеджер утилит для RAG системы строительных материалов
Удобный запуск всех доступных утилит через интерактивное меню
"""

import sys
import os
import asyncio
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

def show_menu():
    """Показать меню доступных утилит"""
    print("\n" + "=" * 60)
    print("🛠️  МЕНЕДЖЕР УТИЛИТ RAG СИСТЕМЫ СТРОИТЕЛЬНЫХ МАТЕРИАЛОВ")
    print("=" * 60)
    print()
    print("📥 ЗАГРУЗКА ДАННЫХ:")
    print("  1. Загрузить строительные материалы из JSON")
    print("  2. Создать тестовые данные")
    print()
    print("🔄 СОПОСТАВЛЕНИЕ МАТЕРИАЛОВ:")
    print("  3. Запустить сопоставление материалов")
    print("  4. Быстрый анализ результатов")
    print("  5. Сохранить полные результаты")
    print("  6. Сохранить упрощенные результаты (CSV)")
    print()
    print("👁️ ПРОСМОТР ДАННЫХ:")
    print("  7. Показать структуру материала")
    print("  8. Проверить загруженные материалы")
    print("  9. Просмотреть коллекции")
    print(" 10. Просмотреть структуру прайсов поставщика")
    print(" 11. Экспорт прайса поставщика в CSV с векторами")
    print()
    print("🧪 ТЕСТИРОВАНИЕ:")
    print(" 12. Тест русского поиска")
    print(" 13. Тест всех сервисов")
    print(" 14. Проверить соединение с БД")
    print()
    print("🗄️ УПРАВЛЕНИЕ:")
    print(" 15. Очистить коллекции")
    print()
    print("  0. Выход")
    print()

async def run_utility(choice: str):
    """Запустить выбранную утилиту"""
    
    try:
        if choice == "1":
            from .load_building_materials import load_materials
            await load_materials()
            
        elif choice == "2":
            from .create_test_data import create_materials
            await create_materials()
            
        elif choice == "3":
            from .material_matcher import main as run_matcher
            await run_matcher()
            
        elif choice == "4":
            from .material_summary import show_material_matches
            supplier_id = input("Введите ID поставщика: ").strip()
            if supplier_id:
                await show_material_matches(supplier_id)
            else:
                print("❌ ID поставщика не указан")
                
        elif choice == "5":
            from .save_matches import save_matches
            await save_matches()
            
        elif choice == "6":
            from .save_simple_matches import save_simple_matches
            supplier_id = input("Введите ID поставщика: ").strip()
            if supplier_id:
                await save_simple_matches(supplier_id)
            else:
                print("❌ ID поставщика не указан")
                
        elif choice == "7":
            exec(open(Path(__file__).parent / "show_material.py").read())
            
        elif choice == "8":
            from .check_loaded_materials import check_materials
            check_materials()
            
        elif choice == "9":
            from .view_collection import main as view_collections
            view_collections()
            
        elif choice == "10":
            from .show_supplier_prices import show_supplier_prices
            supplier_id = input("Введите ID поставщика: ").strip()
            if supplier_id:
                show_supplier_prices(supplier_id)
            else:
                print("❌ ID поставщика не указан")
            
        elif choice == "11":
            from utils.export_supplier_prices import export_supplier_prices_to_csv
            print("\n📋 Экспорт прайса поставщика")
            supplier_id = input("Введите ID поставщика: ").strip()
            if not supplier_id:
                print("❌ ID поставщика не указан")
                return
                
            # Параметры экспорта
            print("\n⚙️ Настройки экспорта:")
            include_vectors = input("Включить векторы? (y/n, по умолчанию y): ").strip().lower()
            include_vectors = include_vectors != 'n'
            
            if include_vectors:
                print("Форматы векторов:")
                print("  json - векторы как JSON строки (компактно)")
                print("  columns - каждое измерение в отдельной колонке (широкая таблица)")
                print("  compact - статистики векторов (норма, среднее, и т.д.)")
                vector_format = input("Формат векторов (json/columns/compact, по умолчанию json): ").strip().lower()
                if vector_format not in ['json', 'columns', 'compact']:
                    vector_format = 'json'
            else:
                vector_format = 'json'
                
            limit_str = input("Ограничить количество записей (Enter - все): ").strip()
            limit = int(limit_str) if limit_str.isdigit() else None
            
            output_file = input("Путь к файлу (Enter - автоматический): ").strip()
            if not output_file:
                output_file = None
                
            # Выполнение экспорта
            result = export_supplier_prices_to_csv(
                supplier_id=supplier_id,
                output_file=output_file,
                include_vectors=include_vectors,
                vector_format=vector_format,
                limit=limit
            )
            
            if not result:
                print("❌ Экспорт не удался")
            
        elif choice == "12":
            from .test_russian_search import main as test_russian
            test_russian()
            
        elif choice == "13":
            from .test_all_services import main as test_services
            await test_services()
            
        elif choice == "14":
            from .check_db_connection import main as check_db
            check_db()
            
        elif choice == "15":
            from .cleanup_collections import main as cleanup
            cleanup()
            
        else:
            print("❌ Неверный выбор")
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что все зависимости установлены")
    except Exception as e:
        print(f"❌ Ошибка выполнения: {e}")

async def main():
    """Основная функция"""
    while True:
        show_menu()
        choice = input("Выберите утилиту (0-15): ").strip()
        
        if choice == "0":
            print("👋 До свидания!")
            break
            
        if choice in [str(i) for i in range(1, 16)]:
            print(f"\n🚀 Запуск утилиты {choice}...")
            print("-" * 40)
            
            await run_utility(choice)
            
            print("\n" + "-" * 40)
            input("Нажмите Enter для продолжения...")
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    asyncio.run(main()) 