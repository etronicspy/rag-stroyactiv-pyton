#!/usr/bin/env python3
"""
Простая утилита для загрузки материалов из JSON файла через API
"""

import json
import requests
import sys

def load_materials_from_json(json_file_path, api_url="http://localhost:8000"):
    """Загрузить материалы из JSON файла через API endpoint"""
    
    print(f"🔄 Загружаю материалы из файла: {json_file_path}")
    
    try:
        # Читаем JSON файл
        with open(json_file_path, 'r', encoding='utf-8') as f:
            materials_data = json.load(f)
        
        print(f"📦 Загружено {len(materials_data)} материалов из файла")
        
        # Подготавливаем запрос для API
        import_request = {
            "materials": materials_data,
            "default_use_category": "Стройматериалы",
            "default_unit": "шт",
            "batch_size": 50
        }
        
        # Отправляем запрос к API
        print(f"🚀 Отправляю запрос к API: {api_url}/api/v1/materials/import")
        
        response = requests.post(
            f"{api_url}/api/v1/materials/import",
            json=import_request,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 минуты timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n✅ Загрузка завершена успешно!")
            print(f"📊 Статистика:")
            print(f"   • Всего обработано: {result['total_processed']}")
            print(f"   • Успешно создано: {len(result['successful_materials'])}")
            print(f"   • Ошибок: {len(result['failed_materials'])}")
            print(f"   • Время обработки: {result['processing_time_seconds']:.2f}с")
            
            if result['failed_materials']:
                print(f"\n❌ Ошибки при создании материалов:")
                for i, failed in enumerate(result['failed_materials'][:5], 1):
                    print(f"   {i}. {failed.get('error', 'Unknown error')}")
                if len(result['failed_materials']) > 5:
                    print(f"   ... и еще {len(result['failed_materials']) - 5} ошибок")
            
            if result.get('errors'):
                print(f"\n⚠️  Общие ошибки:")
                for error in result['errors'][:3]:
                    print(f"   • {error}")
            
            return True
            
        else:
            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"❌ Файл не найден: {json_file_path}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка парсинга JSON: {e}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False

def main():
    """Основная функция"""
    if len(sys.argv) != 2:
        print("Использование: python3 load_materials.py <путь_к_json_файлу>")
        print("Пример: python3 load_materials.py tests/data/building_materials.json")
        sys.exit(1)
    
    json_file_path = sys.argv[1]
    
    print("🏗️  ЗАГРУЗКА СТРОИТЕЛЬНЫХ МАТЕРИАЛОВ")
    print("=" * 50)
    
    success = load_materials_from_json(json_file_path)
    
    if success:
        print(f"\n🎉 Материалы успешно загружены!")
        print(f"💡 Теперь можно протестировать поиск:")
        print(f"   python3 test_search_quality.py")
    else:
        print(f"\n❌ Загрузка не удалась")
        sys.exit(1)

if __name__ == "__main__":
    main() 