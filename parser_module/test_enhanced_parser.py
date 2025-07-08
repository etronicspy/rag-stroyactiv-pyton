"""
Test script for Enhanced AI Parser

This script tests the enhanced AI parser with color extraction and embeddings generation.
"""

import asyncio
import json
import time
import logging
from typing import List, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import enhanced parser
try:
    from enhanced_ai_parser import EnhancedAIParser, create_enhanced_ai_parser, integrate_with_main_project
    from parser_config import ParserConfig
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.info("Trying absolute imports...")
    try:
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from enhanced_ai_parser import EnhancedAIParser, create_enhanced_ai_parser, integrate_with_main_project
        from parser_config import ParserConfig
    except ImportError as e2:
        logger.error(f"Absolute import error: {e2}")
        exit(1)


def test_basic_enhanced_parsing():
    """Test basic enhanced parsing functionality"""
    logger.info("=== Testing Basic Enhanced Parsing ===")
    
    # Create parser with default config
    config = ParserConfig()
    config.enable_debug_logging = True
    parser = EnhancedAIParser(config)
    
    # Test materials with colors
    test_materials = [
        {
            "name": "Цемент белый М500 50кг",
            "unit": "меш",
            "price": 450.0
        },
        {
            "name": "Кирпич красный керамический",
            "unit": "шт", 
            "price": 25.0
        },
        {
            "name": "Песок строительный",
            "unit": "т",
            "price": 1200.0
        },
        {
            "name": "Утеплитель серый 100мм",
            "unit": "м2",
            "price": 150.0
        }
    ]
    
    results = []
    for material in test_materials:
        logger.info(f"Parsing: {material['name']}")
        
        result = parser.parse_material_enhanced(
            name=material["name"],
            unit=material["unit"],
            price=material["price"]
        )
        
        results.append(result)
        
        # Print results
        print(f"\n--- {material['name']} ---")
        print(f"Original unit: {result.original_unit}")
        print(f"Parsed unit: {result.unit_parsed}")
        print(f"Price coefficient: {result.price_coefficient}")
        print(f"Extracted color: {result.color}")
        print(f"Color confidence: {result.color_confidence}")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        # Check embeddings
        if result.color_embedding:
            print(f"Color embedding dimensions: {len(result.color_embedding)}")
        if result.parsed_unit_embedding:
            print(f"Unit embedding dimensions: {len(result.parsed_unit_embedding)}")
        if result.material_embedding:
            print(f"Material embedding dimensions: {len(result.material_embedding)}")
    
    return results


def test_batch_enhanced_parsing():
    """Test batch enhanced parsing"""
    logger.info("=== Testing Batch Enhanced Parsing ===")
    
    # Create parser
    parser = create_enhanced_ai_parser()
    
    # Test materials for batch processing
    batch_materials = [
        {"name": "Цемент белый М400 25кг", "unit": "меш", "price": 300.0},
        {"name": "Кирпич красный полнотелый", "unit": "шт", "price": 30.0},
        {"name": "Блок газобетонный серый 600x300x200", "unit": "шт", "price": 120.0},
        {"name": "Краска белая акриловая 10л", "unit": "вед", "price": 2500.0}
    ]
    
    start_time = time.time()
    results = parser.parse_batch_enhanced(batch_materials)
    batch_time = time.time() - start_time
    
    print(f"\n=== Batch Processing Results ===")
    print(f"Total materials: {len(batch_materials)}")
    print(f"Total processing time: {batch_time:.2f}s")
    print(f"Average time per material: {batch_time/len(batch_materials):.2f}s")
    
    successful_count = sum(1 for r in results if r.success)
    color_extracted_count = sum(1 for r in results if r.color)
    
    print(f"Successful parsings: {successful_count}/{len(results)}")
    print(f"Colors extracted: {color_extracted_count}/{len(results)}")
    
    for i, result in enumerate(results):
        print(f"\n{i+1}. {result.name}")
        print(f"   Unit: {result.original_unit} → {result.unit_parsed}")
        print(f"   Color: {result.color} (conf: {result.color_confidence:.2f})")
        print(f"   Success: {result.success}")
    
    return results


def test_main_project_integration():
    """Test integration with main project"""
    logger.info("=== Testing Main Project Integration ===")
    
    # Try to integrate with main project
    parser = integrate_with_main_project()
    
    if parser is None:
        logger.warning("Main project integration not available")
        return None
    
    logger.info("Main project integration successful!")
    
    # Test with integration
    result = parser.parse_material_enhanced(
        name="Цемент белый М500 Portland",
        unit="кг",
        price=15.0
    )
    
    print(f"\n=== Integration Test Result ===")
    print(f"Name: {result.name}")
    print(f"Color: {result.color}")
    print(f"Unit parsed: {result.unit_parsed}")
    print(f"Embeddings service available: {parser.embedding_service is not None}")
    
    return result


def test_color_extraction_patterns():
    """Test different color extraction patterns"""
    logger.info("=== Testing Color Extraction Patterns ===")
    
    parser = create_enhanced_ai_parser()
    
    # Test various color patterns
    color_test_cases = [
        "Цемент белый М500",
        "Кирпич красный лицевой",
        "Блок серый газобетонный",
        "Краска зеленая фасадная",
        "Утеплитель (без цвета)",
        "Песок желтый речной",
        "Штукатурка черная декоративная"
    ]
    
    print(f"\n=== Color Extraction Test ===")
    for test_case in color_test_cases:
        result = parser.parse_material_enhanced(test_case, "шт")
        color_str = result.color if result.color else "None"
        print(f"{test_case:<30} → {color_str:<10} (conf: {result.color_confidence:.2f})")


def test_embeddings_generation():
    """Test embeddings generation specifically"""
    logger.info("=== Testing Embeddings Generation ===")
    
    parser = create_enhanced_ai_parser()
    
    # Test single material with detailed embeddings analysis
    result = parser.parse_material_enhanced(
        name="Цемент портландский белый М500 50кг",
        unit="меш",
        price=500.0
    )
    
    print(f"\n=== Embeddings Analysis ===")
    print(f"Material: {result.name}")
    print(f"Color: {result.color}")
    print(f"Parsed unit: {result.unit_parsed}")
    
    # Analyze embeddings
    embeddings_info = {
        "Color embedding": result.color_embedding,
        "Unit embedding": result.parsed_unit_embedding,
        "Material embedding": result.material_embedding
    }
    
    for name, embedding in embeddings_info.items():
        if embedding:
            print(f"{name}: {len(embedding)} dimensions")
            print(f"  Sample values: {embedding[:5]}")  # First 5 values
            print(f"  Min: {min(embedding):.4f}, Max: {max(embedding):.4f}")
        else:
            print(f"{name}: Not generated")


def test_statistics():
    """Test parser statistics"""
    logger.info("=== Testing Parser Statistics ===")
    
    parser = create_enhanced_ai_parser()
    
    # Perform some parsing operations
    test_materials = [
        ("Цемент белый", "кг"),
        ("Кирпич красный", "шт"),
        ("Песок", "т")
    ]
    
    for name, unit in test_materials:
        parser.parse_material_enhanced(name, unit)
    
    # Get statistics
    stats = parser.get_enhanced_statistics()
    
    print(f"\n=== Parser Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")


def main():
    """Run all tests"""
    print("🚀 Enhanced AI Parser Testing Suite")
    print("=" * 50)
    
    try:
        # Run basic tests
        test_basic_enhanced_parsing()
        
        # Run batch test
        test_batch_enhanced_parsing()
        
        # Test color extraction
        test_color_extraction_patterns()
        
        # Test embeddings
        test_embeddings_generation()
        
        # Test statistics
        test_statistics()
        
        # Try main project integration
        test_main_project_integration()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main() 