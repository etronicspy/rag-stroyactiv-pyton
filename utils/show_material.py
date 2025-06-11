import requests
import json

# Запрос к API - используем актуальный ID материала с новой структурой
response = requests.get('http://localhost:8000/api/v1/materials/0124bbd7-37b6-4e22-b21e-952f416a87a0')
data = response.json()

print('=== ПОЛНАЯ СТРУКТУРА МАТЕРИАЛА ===')
print(f'🆔 ID: {data["id"]}')
print(f'📦 Name: {data["name"]}')
print(f'🏷️ Category: {data["use_category"]}')
print(f'📏 Unit: {data["unit"]}')
print(f'🔖 SKU: {data["sku"]}')
print(f'📝 Description: {data["description"]}')
print(f'🧠 Embedding: {"✅ Есть" if data["embedding"] else "❌ Нет"} ({len(data["embedding"]) if data["embedding"] else 0} размерностей)')
print(f'📅 Created: {data["created_at"]}')
print(f'🔄 Updated: {data["updated_at"]}')
print()

if data["embedding"]:
    print(f'🔢 Vector preview (первые 10): {data["embedding"][:10]}')
    print(f'📊 Vector type: {type(data["embedding"])}')
    print(f'📈 Vector stats: min={min(data["embedding"]):.6f}, max={max(data["embedding"]):.6f}')

print()
print('=== JSON STRUCTURE ===')
print(json.dumps(data, ensure_ascii=False, indent=2)[:500] + '...') 