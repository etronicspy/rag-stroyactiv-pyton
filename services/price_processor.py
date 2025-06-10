from typing import List, Dict, Any
import pandas as pd
from core.models.materials import Material, Category, Unit

class PriceProcessor:
    def __init__(self):
        self.required_columns = ['name', 'category', 'unit']
    
    async def process_price_list(self, file_path: str) -> Dict[str, Any]:
        try:
            # Read the file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                return {"success": False, "error": "Unsupported file format"}
            
            # Validate columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing_columns)}"
                }
            
            # Process materials
            materials = []
            errors = []
            
            for idx, row in df.iterrows():
                try:
                    material = {
                        "name": str(row['name']).strip(),
                        "category": str(row['category']).strip(),
                        "unit": str(row['unit']).strip(),
                        "description": str(row.get('description', '')).strip()
                    }
                    
                    # Validate material data
                    if len(material['name']) < 2 or len(material['name']) > 200:
                        raise ValueError(f"Invalid name length for material at row {idx + 1}")
                    
                    # Add to materials list
                    materials.append(material)
                    
                except Exception as e:
                    errors.append(f"Error in row {idx + 1}: {str(e)}")
            
            return {
                "success": True,
                "materials": materials,
                "errors": errors,
                "total_processed": len(df),
                "successful": len(materials),
                "failed": len(errors)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    async def validate_categories(categories: List[str]) -> List[str]:
        """Validate categories against existing ones in database"""
        existing_categories = await Category.find_all().to_list()
        existing_names = {cat.name for cat in existing_categories}
        return [cat for cat in categories if cat not in existing_names]
    
    @staticmethod
    async def validate_units(units: List[str]) -> List[str]:
        """Validate units against existing ones in database"""
        existing_units = await Unit.find_all().to_list()
        existing_names = {unit.name for unit in existing_units}
        return [unit for unit in units if unit not in existing_names] 