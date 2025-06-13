"""
Общие тестовые данные для всех типов тестов
"""
from typing import Dict, List, Any
from datetime import datetime


class TestDataProvider:
    """Поставщик тестовых данных"""
    
    @staticmethod
    def get_sample_materials() -> List[Dict[str, Any]]:
        """Образцы материалов для тестирования"""
        return [
            {
                "name": "Portland Cement M400 Test",
                "use_category": "Building Materials",
                "unit": "kg",
                "price": 45.50,
                "description": "High quality Portland cement M400 for testing",
                "sku": "CEM001_TEST"
            },
            {
                "name": "Construction Sand Test",
                "use_category": "Building Materials", 
                "unit": "m3",
                "price": 1200.00,
                "description": "Washed construction sand for testing",
                "sku": "SAND001_TEST"
            },
            {
                "name": "Steel Rebar 12mm Test",
                "use_category": "Steel Products",
                "unit": "m",
                "price": 78.90,
                "description": "Steel reinforcement bar 12mm diameter for testing",
                "sku": "REBAR012_TEST"
            },
            {
                "name": "Brick Red Clay Test",
                "use_category": "Masonry",
                "unit": "pcs",
                "price": 5.25,
                "description": "Red clay brick standard size for testing",
                "sku": "BRICK001_TEST"
            }
        ]
    
    @staticmethod
    def get_sample_categories() -> List[Dict[str, str]]:
        """Образцы категорий для тестирования"""
        return [
            {
                "name": "Building Materials",
                "description": "Basic construction materials like cement, sand, gravel"
            },
            {
                "name": "Steel Products", 
                "description": "Steel bars, beams, sheets and other steel products"
            },
            {
                "name": "Masonry",
                "description": "Bricks, blocks, tiles and masonry materials"
            },
            {
                "name": "Insulation",
                "description": "Thermal and sound insulation materials"
            }
        ]
    
    @staticmethod
    def get_sample_units() -> List[Dict[str, str]]:
        """Образцы единиц измерения для тестирования"""
        return [
            {
                "name": "kg",
                "description": "Kilogram - unit of mass"
            },
            {
                "name": "m3",
                "description": "Cubic meter - unit of volume"
            },
            {
                "name": "m",
                "description": "Meter - unit of length"
            },
            {
                "name": "pcs",
                "description": "Pieces - counting unit"
            },
            {
                "name": "m2",
                "description": "Square meter - unit of area"
            }
        ]
    
    @staticmethod
    def get_price_list_csv_data() -> str:
        """CSV данные для тестирования загрузки прайс-листов"""
        return """name,use_category,unit,price,description
Portland Cement M400,Building Materials,kg,45.50,High quality Portland cement M400
Construction Sand Washed,Building Materials,m3,1200.00,Washed construction sand
Steel Rebar 12mm,Steel Products,m,78.90,Steel reinforcement bar 12mm diameter
Red Clay Brick,Masonry,pcs,5.25,Red clay brick standard size
Mineral Wool Insulation,Insulation,m2,125.00,Thermal insulation mineral wool"""
    
    @staticmethod
    def get_search_queries() -> List[Dict[str, Any]]:
        """Тестовые поисковые запросы"""
        return [
            {
                "query": "cement",
                "expected_results": ["Portland Cement", "cement"],
                "description": "Basic material search"
            },
            {
                "query": "steel reinforcement",
                "expected_results": ["Steel Rebar", "reinforcement"],
                "description": "Multi-word search"
            },
            {
                "query": "изоляция",
                "expected_results": ["insulation", "изоляция"],
                "description": "Russian language search"
            }
        ]
    
    @staticmethod
    def get_invalid_data_samples() -> Dict[str, List[Dict[str, Any]]]:
        """Образцы некорректных данных для тестирования валидации"""
        return {
            "missing_required_fields": [
                {
                    "use_category": "Building Materials",
                    "unit": "kg",
                    "price": 45.50
                    # Отсутствует name
                },
                {
                    "name": "Test Material",
                    "unit": "kg", 
                    "price": 45.50
                    # Отсутствует use_category
                }
            ],
            "invalid_types": [
                {
                    "name": "Test Material",
                    "use_category": "Building Materials",
                    "unit": "kg",
                    "price": "invalid_price",  # Строка вместо числа
                    "description": "Test description"
                }
            ],
            "invalid_values": [
                {
                    "name": "",  # Пустое название
                    "use_category": "Building Materials",
                    "unit": "kg",
                    "price": 45.50,
                    "description": "Test description"
                },
                {
                    "name": "Test Material",
                    "use_category": "Building Materials",
                    "unit": "kg",
                    "price": -45.50,  # Отрицательная цена
                    "description": "Test description"
                }
            ]
        }
    
    @staticmethod
    def get_supplier_data() -> Dict[str, Any]:
        """Данные поставщика для тестирования"""
        return {
            "supplier_id": "TEST_SUPPLIER_001",
            "name": "Test Construction Supplier Ltd.",
            "contact_info": {
                "email": "test@supplier.com",
                "phone": "+1234567890",
                "address": "123 Test Street, Test City"
            },
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "test_flag": True
            }
        }
    
    @staticmethod
    def get_embedding_vectors() -> Dict[str, List[float]]:
        """Тестовые векторы эмбеддингов"""
        return {
            "cement_vector": [0.1] * 1536,  # OpenAI text-embedding-3-small размер
            "steel_vector": [0.2] * 1536,
            "brick_vector": [0.3] * 1536,
            "sand_vector": [0.4] * 1536
        }
    
    @staticmethod
    def get_batch_operations_data() -> Dict[str, Any]:
        """Данные для тестирования batch операций"""
        return {
            "small_batch": TestDataProvider.get_sample_materials()[:2],
            "medium_batch": TestDataProvider.get_sample_materials() * 5,  # 20 items
            "large_batch": TestDataProvider.get_sample_materials() * 25,  # 100 items
            "batch_size_limits": {
                "default": 50,
                "small": 10,
                "large": 100
            }
        } 