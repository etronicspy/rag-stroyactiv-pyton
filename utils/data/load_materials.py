"""
Utility for loading materials from JSON file to database
"""
import json
import asyncio
import aiohttp
from typing import List, Dict, Any
from pathlib import Path

class MaterialsLoader:
    """Utility class for loading materials from JSON files"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api/v1/materials"
    
    async def load_from_json_file(self, file_path: str, batch_size: int = 100) -> Dict[str, Any]:
        """Load materials from JSON file using the import API"""
        try:
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                materials_data = json.load(f)
            
            print(f"Loaded {len(materials_data)} materials from {file_path}")
            
            # Prepare import request
            import_request = {
                "materials": materials_data,
                "default_category": "Стройматериалы",
                "default_unit": "шт",
                "batch_size": batch_size
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/import",
                    json=import_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Import successful!")
                        print(f"Total processed: {result['total_processed']}")
                        print(f"Successful creates: {result['successful_creates']}")
                        print(f"Failed creates: {result['failed_creates']}")
                        print(f"Processing time: {result['processing_time_seconds']}s")
                        
                        if result['errors']:
                            print(f"❌ Errors ({len(result['errors'])}):")
                            for error in result['errors'][:5]:  # Show first 5 errors
                                print(f"  - {error}")
                        
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ Import failed with status {response.status}: {error_text}")
                        return {"success": False, "error": error_text}
                        
        except Exception as e:
            print(f"❌ Error loading materials: {e}")
            return {"success": False, "error": str(e)}
    
    async def load_using_batch_api(self, materials: List[Dict[str, Any]], batch_size: int = 100) -> Dict[str, Any]:
        """Load materials using the batch API directly"""
        try:
            # Prepare batch request
            batch_request = {
                "materials": materials,
                "batch_size": batch_size
            }
            
            # Make API request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/batch",
                    json=batch_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Batch creation successful!")
                        print(f"Total processed: {result['total_processed']}")
                        print(f"Successful creates: {result['successful_creates']}")
                        print(f"Failed creates: {result['failed_creates']}")
                        print(f"Processing time: {result['processing_time_seconds']}s")
                        
                        if result['errors']:
                            print(f"❌ Errors ({len(result['errors'])}):")
                            for error in result['errors'][:5]:  # Show first 5 errors
                                print(f"  - {error}")
                        
                        return result
                    else:
                        error_text = await response.text()
                        print(f"❌ Batch creation failed with status {response.status}: {error_text}")
                        return {"success": False, "error": error_text}
                        
        except Exception as e:
            print(f"❌ Error in batch creation: {e}")
            return {"success": False, "error": str(e)}
    
    async def check_api_status(self) -> bool:
        """Check if API is available"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/v1/health/") as response:
                    return response.status == 200
        except Exception:
            return False
    
    def convert_json_format(self, materials_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert JSON format from {sku, name} to MaterialCreate format"""
        converted = []
        for item in materials_data:
            # Auto-categorize based on name
            category = self._infer_category(item['name'])
            unit = self._infer_unit(item['name'])
            
            converted.append({
                "name": item['name'],
                "category": category,
                "unit": unit,
                "sku": item['sku'],
                "description": None
            })
        return converted
    
    def _infer_category(self, name: str) -> str:
        """Infer category from material name"""
        name_lower = name.lower()
        
        category_keywords = {
            "цемент": "Цемент",
            "бетон": "Бетон", 
            "кирпич": "Кирпич",
            "блок": "Блоки",
            "песок": "Песок",
            "щебень": "Щебень",
            "арматура": "Арматура",
            "металл": "Металлопрокат",
            "доска": "Пиломатериалы",
            "брус": "Пиломатериалы",
            "фанера": "Листовые материалы",
            "гипсокартон": "Листовые материалы",
            "плитка": "Плитка",
            "краска": "Лакокрасочные материалы",
            "эмаль": "Лакокрасочные материалы",
            "шпатлевка": "Сухие смеси",
            "штукатурка": "Сухие смеси",
            "утеплитель": "Теплоизоляция",
            "черепица": "Кровельные материалы",
            "профнастил": "Кровельные материалы",
            "труба": "Трубы и фитинги",
            "кабель": "Электротехника",
            "провод": "Электротехника",
            "окно": "Окна и двери",
            "дверь": "Окна и двери",
            "саморез": "Крепеж",
            "гвоздь": "Крепеж",
            "болт": "Крепеж"
        }
        
        for keyword, category in category_keywords.items():
            if keyword in name_lower:
                return category
        
        return "Стройматериалы"
    
    def _infer_unit(self, name: str) -> str:
        """Infer unit from material name"""
        name_lower = name.lower()
        
        unit_keywords = {
            "цемент": "кг",
            "песок": "м³",
            "щебень": "м³",
            "бетон": "м³",
            "доска": "м³",
            "брус": "м³",
            "кирпич": "шт",
            "блок": "шт",
            "плитка": "м²",
            "краска": "кг",
            "эмаль": "кг",
            "лист": "м²",
            "рулон": "м²",
            "труба": "м",
            "кабель": "м",
            "провод": "м"
        }
        
        for keyword, unit in unit_keywords.items():
            if keyword in name_lower:
                return unit
        
        return "шт"

async def main():
    """Main function for command line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load materials from JSON file to the API")
    parser.add_argument("json_file", help="Path to JSON file with materials")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for processing (default: 100)")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL of the API (default: http://localhost:8000)")
    
    args = parser.parse_args()
    
    file_path = args.json_file
    batch_size = args.batch_size
    base_url = args.base_url
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    
    loader = MaterialsLoader(base_url)
    
    # Check API availability
    print("Checking API availability...")
    if not await loader.check_api_status():
        print(f"❌ API is not available at {base_url}")
        sys.exit(1)
    
    print(f"✅ API is available at {base_url}")
    
    # Load materials
    print(f"Loading materials from {file_path}...")
    result = await loader.load_from_json_file(file_path, batch_size)
    
    if result.get("success"):
        print("🎉 Materials loaded successfully!")
    else:
        print("❌ Failed to load materials")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 