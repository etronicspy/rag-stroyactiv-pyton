#!/usr/bin/env python3
import asyncio
from .load_materials import MaterialsLoader

async def load_materials():
    """Загрузка строительных материалов из JSON файла"""
    loader = MaterialsLoader()
    
    print('🔍 Проверяю доступность API...')
    if not await loader.check_api_status():
        print('❌ API недоступен! Убедитесь, что сервер запущен на порту 8000')
        return
    
    print('✅ API доступен')
    print('📥 Начинаю загрузку материалов из tests/data/building_materials.json...')
    
    result = await loader.load_from_json_file(
        'tests/data/building_materials.json', 
        batch_size=50
    )
    
    if result.get('success', False):
        print('🎉 Загрузка завершена успешно!')
    else:
        print('❌ Загрузка завершена с ошибками')
    
    return result

if __name__ == "__main__":
    asyncio.run(load_materials()) 