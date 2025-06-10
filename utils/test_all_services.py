#!/usr/bin/env python3
"""Test script to check all services and collection auto-creation"""

import sys
import os
from pathlib import Path
import asyncio

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.materials import MaterialsService, CategoryService, UnitService
from core.schemas.materials import MaterialCreate

async def test_category_service():
    """Test CategoryService"""
    print("\n🏷️  Testing CategoryService...")
    try:
        service = CategoryService()
        print("✅ CategoryService initialized")
        
        # Create test category
        category = await service.create_category("Тестовая категория", "Описание тестовой категории")
        print(f"✅ Category created: {category.name}")
        
        # Get all categories
        categories = await service.get_categories()
        print(f"✅ Retrieved {len(categories)} categories")
        
        return True
    except Exception as e:
        print(f"❌ CategoryService error: {e}")
        return False

async def test_unit_service():
    """Test UnitService"""
    print("\n📏 Testing UnitService...")
    try:
        service = UnitService()
        print("✅ UnitService initialized")
        
        # Create test unit
        unit = await service.create_unit("тест", "Тестовая единица измерения")
        print(f"✅ Unit created: {unit.name}")
        
        # Get all units
        units = await service.get_units()
        print(f"✅ Retrieved {len(units)} units")
        
        return True
    except Exception as e:
        print(f"❌ UnitService error: {e}")
        return False

async def test_materials_service():
    """Test MaterialsService"""
    print("\n🧱 Testing MaterialsService...")
    try:
        service = MaterialsService()
        print("✅ MaterialsService initialized")
        
        # Create test material
        material_data = MaterialCreate(
            name="Тестовый материал",
            category="Тестовая категория",
            unit="тест",
            description="Описание тестового материала"
        )
        material = await service.create_material(material_data)
        print(f"✅ Material created: {material.name} (ID: {material.id})")
        
        # Get all materials
        materials = await service.get_materials(limit=10)
        print(f"✅ Retrieved {len(materials)} materials")
        
        # Test search
        search_results = await service.search_materials("тест", limit=5)
        print(f"✅ Search returned {len(search_results)} results")
        
        return True
    except Exception as e:
        print(f"❌ MaterialsService error: {e}")
        return False

async def check_collections():
    """Check what collections exist"""
    print("\n📂 Checking existing collections...")
    try:
        from core.config import get_vector_db_client
        client = get_vector_db_client()
        
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"📋 Found {len(collection_names)} collections:")
        for name in collection_names:
            print(f"  • {name}")
        
        return collection_names
    except Exception as e:
        print(f"❌ Error checking collections: {e}")
        return []

async def main():
    """Main test function"""
    print("🧪 Testing All Services with Auto Collection Creation")
    print("=" * 60)
    
    # Check initial collections
    initial_collections = await check_collections()
    
    # Test all services
    category_ok = await test_category_service()
    unit_ok = await test_unit_service()
    materials_ok = await test_materials_service()
    
    # Check final collections
    print("\n" + "=" * 60)
    final_collections = await check_collections()
    
    # Summary
    print(f"\n📊 Test Results:")
    print(f"  CategoryService: {'✅ PASS' if category_ok else '❌ FAIL'}")
    print(f"  UnitService: {'✅ PASS' if unit_ok else '❌ FAIL'}")
    print(f"  MaterialsService: {'✅ PASS' if materials_ok else '❌ FAIL'}")
    
    new_collections = set(final_collections) - set(initial_collections)
    if new_collections:
        print(f"\n🆕 New collections created: {', '.join(new_collections)}")
    else:
        print(f"\n🔄 Collections were reused or already existed")
    
    overall_success = category_ok and unit_ok and materials_ok
    print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return overall_success

if __name__ == "__main__":
    asyncio.run(main()) 