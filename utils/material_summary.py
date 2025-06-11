#!/usr/bin/env python3
"""
Утилита для быстрого просмотра результатов сопоставления материалов (оптимизировано)

Показывает статистику и лучшие совпадения без сохранения в базу данных.
"""

import asyncio

from .material_matcher import MaterialMatcher
from .common import truncate_text, format_price

async def show_material_matches(supplier_id: str):
    """Показать результаты сопоставления материалов (оптимизированная версия)"""
    
    print("🔍 ОПТИМИЗИРОВАННЫЙ АНАЛИЗ СОПОСТАВЛЕНИЯ МАТЕРИАЛОВ")
    print("="*60)
    print(f"📦 Поставщик: {supplier_id}")
    print("="*60)
    
    matcher = MaterialMatcher()
    
    try:
        # Оптимизированное сопоставление с параллельным векторным поиском
        matches = await matcher.match_materials_with_vector_search(supplier_id, top_k=5)
        
        if not matches:
            print("❌ Сопоставления не найдены")
            return
        
        # Статистика по уровням уверенности
        high_conf = [m for m in matches if m.match_confidence == "high"]
        medium_conf = [m for m in matches if m.match_confidence == "medium"] 
        low_conf = [m for m in matches if m.match_confidence == "low"]
        
        print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
        print(f"   🎯 Всего материалов в прайсе: {len(matches)}")
        print(f"   ✅ Высокая уверенность: {len(high_conf)} ({len(high_conf)/len(matches)*100:.1f}%)")
        print(f"   🟡 Средняя уверенность: {len(medium_conf)} ({len(medium_conf)/len(matches)*100:.1f}%)")
        print(f"   🔴 Низкая уверенность: {len(low_conf)} ({len(low_conf)/len(matches)*100:.1f}%)")
        
        avg_score = sum(m.combined_score for m in matches) / len(matches)
        print(f"   📈 Средний скор сходства: {avg_score:.3f}")
        
        # Детальный список совпадений
        print(f"\n🎯 ДЕТАЛЬНЫЕ РЕЗУЛЬТАТЫ:")
        print("-"*120)
        print(f"{'№':>2} {'Материал из прайса':<30} {'→':<2} {'Эталонный материал':<30} {'Скор':>6} {'Ув-ть':>8} {'Цена':>10}")
        print("-"*120)
        
        for i, match in enumerate(matches, 1):
            confidence_icon = {"high": "🟢", "medium": "🟡", "low": "🔴"}[match.match_confidence]
            
            price_name = truncate_text(match.price_item_name, 30)
            ref_name = truncate_text(match.reference_name, 30)
            price_formatted = format_price(match.price_item_price)
            
            print(f"{i:>2} {price_name:<30} → {ref_name:<30} {match.combined_score:>6.3f} {confidence_icon}{match.match_confidence:>7} {price_formatted:>10}")
        
        # Анализ единиц измерения
        print(f"\n📏 АНАЛИЗ ЕДИНИЦ ИЗМЕРЕНИЯ:")
        unit_matches = {}
        for match in matches:
            unit_pair = (match.price_item_unit, match.reference_unit)
            if unit_pair not in unit_matches:
                unit_matches[unit_pair] = []
            unit_matches[unit_pair].append(match.unit_similarity)
        
        for (price_unit, ref_unit), similarities in unit_matches.items():
            avg_sim = sum(similarities) / len(similarities)
            match_icon = "✅" if price_unit == ref_unit else "⚠️"
            print(f"   {match_icon} {price_unit} → {ref_unit}: {avg_sim:.3f} сходство ({len(similarities)} материалов)")
        
        # Категории
        print(f"\n📂 АНАЛИЗ КАТЕГОРИЙ:")
        category_matches = {}
        for match in matches:
            cat_pair = (match.price_item_category, match.reference_category)
            if cat_pair not in category_matches:
                category_matches[cat_pair] = 0
            category_matches[cat_pair] += 1
        
        for (price_cat, ref_cat), count in category_matches.items():
            match_icon = "✅" if price_cat == ref_cat else "⚠️"
            print(f"   {match_icon} {price_cat} → {ref_cat}: {count} материалов")
        
        print(f"\n🎉 АНАЛИЗ ЗАВЕРШЕН")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

async def main():
    """Главная функция"""
    supplier_id = "Поставщик_Строй_Материалы"
    await show_material_matches(supplier_id)

if __name__ == "__main__":
    asyncio.run(main()) 