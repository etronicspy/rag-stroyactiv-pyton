import requests
import json

# Запрос к API для реального материала с sku
response = requests.get('http://localhost:8000/api/v1/materials/0031014c-2034-4963-9ff6-ecca63565954')
data = response.json()

print('=== СТРУКТУРА РЕАЛЬНОГО МАТЕРИАЛА ИЗ ИМПОРТА ===')
print(f'🆔 ID: {data["id"]}')
print(f'📦 Name: {data["name"]}')
print(f'🏷️ Category: {data["category"]}')
print(f'📏 Unit: {data["unit"]}')
print(f'📝 Description: {data["description"]}')
print(f'🧠 Embedding: {"✅ Есть" if data["embedding"] else "❌ Нет"} ({len(data["embedding"]) if data["embedding"] else 0} размерностей)')
print(f'📅 Created: {data["created_at"]}')
print(f'🔄 Updated: {data["updated_at"]}')
print()

if data["embedding"]:
    print(f'🔢 Vector preview (первые 10): {data["embedding"][:10]}')
    print(f'📊 Vector последние 5: {data["embedding"][-5:]}')
    print(f'📈 Vector stats: min={min(data["embedding"]):.6f}, max={max(data["embedding"]):.6f}')
    print(f'📐 Vector norm: {sum(x*x for x in data["embedding"])**0.5:.6f}')

print()
print('=== СРАВНЕНИЕ С QDRANT СТРУКТУРОЙ ===')
print('✅ Qdrant хранит:')
print('   - ID (UUID4)')
print('   - Payload: {name, category, unit, description, created_at, updated_at}')
print('   - Vector: [1536 float32 значений] - OpenAI embedding')
print()
print('✅ API возвращает:')
print('   - Все поля из payload')
print('   - ID как строку')
print('   - Vector как массив чисел')
print('   - Timestamps в ISO формате') 