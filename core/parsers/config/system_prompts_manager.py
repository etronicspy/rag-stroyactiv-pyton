"""
System Prompts Manager

Advanced management system for AI prompts with dynamic optimization,
caching, and context-aware prompt generation.
"""

import json
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from functools import lru_cache
from dataclasses import dataclass, field
from enum import Enum
import re

# Core infrastructure imports
from core.config.parsers import ParserConfig, get_parser_config
from core.config.constants import ParserConstants
from core.logging.specialized.parsers import get_material_parser_logger

# Legacy compatibility imports
try:
    from parser_module.system_prompts import (
        get_material_parsing_system_prompt,
        get_material_parsing_user_prompt,
        get_embeddings_system_prompt,
        MATERIAL_TYPE_PROMPTS,
        UNIT_PARSING_PATTERNS
    )
    LEGACY_PROMPTS_AVAILABLE = True
except ImportError:
    LEGACY_PROMPTS_AVAILABLE = False


class PromptType(Enum):
    """Types of prompts available in the system"""
    SYSTEM_PROMPT = "system_prompt"
    USER_PROMPT = "user_prompt"
    EMBEDDINGS_PROMPT = "embeddings_prompt"
    SPECIALIZED_PROMPT = "specialized_prompt"


@dataclass
class PromptTemplate:
    """Template for prompt generation"""
    name: str
    type: PromptType
    template: str
    variables: List[str] = field(default_factory=list)
    description: str = ""
    version: str = "1.0.0"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    usage_count: int = 0
    success_rate: float = 0.0
    
    def render(self, **kwargs) -> str:
        """Render prompt template with variables"""
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Missing variable {e} for prompt template '{self.name}'")
    
    def validate_variables(self, **kwargs) -> bool:
        """Validate that all required variables are provided"""
        return all(var in kwargs for var in self.variables)
    
    def update_usage_stats(self, success: bool) -> None:
        """Update usage statistics"""
        self.usage_count += 1
        # Simple moving average for success rate
        if self.usage_count == 1:
            self.success_rate = 1.0 if success else 0.0
        else:
            self.success_rate = (self.success_rate * (self.usage_count - 1) + (1.0 if success else 0.0)) / self.usage_count
        self.updated_at = time.time()


@dataclass
class PromptOptimizationContext:
    """Context for prompt optimization"""
    language: str = "russian"
    domain: str = "construction"
    material_type: Optional[str] = None
    complexity_level: str = "medium"
    target_confidence: float = 0.8
    enable_color_extraction: bool = True
    enable_embeddings: bool = True


class SystemPromptsManager:
    """
    Advanced system prompts manager.
    
    Provides dynamic prompt generation, optimization, caching, and
    context-aware prompt selection for AI parsing operations.
    """
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """
        Initialize System Prompts Manager.
        
        Args:
            config: Optional parser configuration
        """
        self.config = config or get_parser_config()
        self.logger = get_material_parser_logger()
        
        # Prompt templates storage
        self._templates: Dict[str, PromptTemplate] = {}
        
        # Prompt cache
        self._prompt_cache: Dict[str, str] = {}
        self._cache_max_size = 1000
        
        # Optimization context
        self._default_context = PromptOptimizationContext()
        
        # Service metadata
        self._service_name = "system_prompts_manager"
        self._version = "2.0.0"
        
        # Statistics
        self.stats = {
            "total_prompts_generated": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "optimization_requests": 0,
            "template_updates": 0
        }
        
        # Initialize default templates
        self._initialize_default_templates()
        
        self.logger.info(f"System Prompts Manager v{self._version} initialized")
    
    def _initialize_default_templates(self):
        """Initialize default prompt templates"""
        
        # System prompt template
        system_template = PromptTemplate(
            name="material_parsing_system",
            type=PromptType.SYSTEM_PROMPT,
            template=self._get_default_system_prompt(),
            variables=["common_units"],
            description="Main system prompt for material parsing"
        )
        self._templates[system_template.name] = system_template
        
        # User prompt template
        user_template = PromptTemplate(
            name="material_parsing_user",
            type=PromptType.USER_PROMPT,
            template=self._get_default_user_prompt(),
            variables=["name", "unit", "material_hint", "is_block"],
            description="User prompt for specific material parsing"
        )
        self._templates[user_template.name] = user_template
        
        # Embeddings prompt template
        embeddings_template = PromptTemplate(
            name="embeddings_generation",
            type=PromptType.EMBEDDINGS_PROMPT,
            template=self._get_default_embeddings_prompt(),
            variables=[],
            description="Prompt for embeddings generation"
        )
        self._templates[embeddings_template.name] = embeddings_template
        
        # Specialized prompts
        self._initialize_specialized_templates()
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt"""
        if LEGACY_PROMPTS_AVAILABLE:
            return """
Ты эксперт по строительным материалам. Анализируй названия товаров и извлекай метрические единицы измерения.

ВОЗВРАЩАЙ ТОЛЬКО ВАЛИДНЫЙ JSON в формате:
{{
    "unit_parsed": "единица_измерения",
    "price_coefficient": число,
    "confidence": число_от_0_до_1,
    "color": "цвет_или_null"
}}

ПОДДЕРЖИВАЕМЫЕ ЕДИНИЦЫ: {common_units}

ВАЖНО! ЛОГИКА КОЭФФИЦИЕНТА:
price_coefficient = количество метрических единиц в 1 исходной единице
Примеры:
- "Цемент 50кг" (продается за мешок) → коэффициент 50 (в 1 мешке = 50 кг)
- "Кирпич объемом 0.00195 м³" (продается за штуку) → коэффициент 0.00195 (в 1 шт = 0.00195 м³)

ПРАВИЛА ИЗВЛЕЧЕНИЯ:
1. Явные единицы: "50кг" → кг, коэффициент 50
2. БЛОЧНЫЕ МАТЕРИАЛЫ → ВСЕГДА м3 (объем):
   - Кирпич, газобетон, пеноблок, шлакоблок, керамзитобетон
   - Блоки, камни, бруски, плиты, панели, элементы, модули
   - Если есть размеры → рассчитать объем в м³
   - Если нет размеров → стандартный объем (например, кирпич = 0.00195 м³)
3. Размеры для объема: "600x300x200" → м3, рассчитать объем в м³
4. Размеры для площади: листы/плиты ≤50мм → м2, рассчитать площадь в м²
5. Жидкости: "850мл" → л, перевести в литры
6. Рулоны: "1x15м" → м2, рассчитать площадь
7. Если единица не извлекается → "шт", коэффициент 1.0

ИЗВЛЕЧЕНИЕ ЦВЕТА:
8. Ищи цвет в названии материала:
   - БАЗОВЫЕ ЦВЕТА: белый, черный, серый, красный, синий, зеленый, желтый, коричневый, оранжевый
   - ОТТЕНКИ: светлый, темный, яркий, матовый, глянцевый
   - ПРИРОДНЫЕ: бежевый, песочный, терракотовый, кирпичный, древесный
   - Если цвет НЕ найден → "color": null
   - Если найден → "color": "название_цвета"

РАСЧЕТЫ:
- Объем (м³): длина×ширина×высота ÷ 1,000,000,000 (если размеры в мм)
- Площадь (м²): длина×ширина ÷ 1,000,000 (если размеры в мм)
- Стандартный кирпич: 250×120×65мм = 0.00195 м³
- Стандартный газобетонный блок: 600×300×200мм = 0.036 м³

CONFIDENCE:
- 0.9+ : явные единицы в названии
- 0.7-0.9 : размеры с явным контекстом или известный блочный материал
- 0.5-0.7 : размеры без четкого контекста
- 0.3-0.5 : предположения по типу материала
- <0.3 : сложные случаи

Отвечай ТОЛЬКО JSON без дополнительного текста.
"""
        else:
            return """
You are an expert in construction materials. Analyze product names and extract metric units.

RETURN ONLY VALID JSON in format:
{{
    "unit_parsed": "unit",
    "price_coefficient": number,
    "confidence": number_from_0_to_1,
    "color": "color_or_null"
}}

SUPPORTED UNITS: {common_units}

COEFFICIENT LOGIC:
price_coefficient = number of metric units in 1 original unit

Return ONLY JSON without additional text.
"""
    
    def _get_default_user_prompt(self) -> str:
        """Get default user prompt"""
        return """
Товар: "{name}"
Единица в прайсе: "{unit}"
Цена: Указана за единицу "{unit}"
{material_hint}
{block_hint}

Извлеки метрическую единицу измерения и рассчитай коэффициент для пересчета цены.
"""
    
    def _get_default_embeddings_prompt(self) -> str:
        """Get default embeddings prompt"""
        return """
Ты создаешь эмбеддинги для строительных материалов. 
Фокусируйся на ключевых характеристиках материала:
- Тип материала (цемент, кирпич, утеплитель и т.д.)
- Назначение (строительство, отделка, изоляция)
- Основные свойства (прочность, теплоизоляция, водостойкость)
- Размеры и форма
- Материал изготовления
"""
    
    def _initialize_specialized_templates(self):
        """Initialize specialized prompt templates"""
        specialized_prompts = {
            "block_materials": """
БЛОЧНЫЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
- Всегда переводить в м³ (объем)
- Рассчитывать объем по размерам если указаны
- Использовать стандартные объемы для типовых изделий
- Примеры: кирпич, газобетон, пеноблок, шлакоблок
            """,
            
            "liquid_materials": """
ЖИДКИЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
- Переводить в литры (л)
- Учитывать плотность для расчета объема
- Примеры: краски, лаки, грунтовки, растворители
            """,
            
            "sheet_materials": """
ЛИСТОВЫЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
- Переводить в м² (площадь)
- Рассчитывать площадь по размерам листа
- Примеры: фанера, OSB, гипсокартон, профлист
            """,
            
            "bulk_materials": """
СЫПУЧИЕ МАТЕРИАЛЫ - СПЕЦИАЛЬНЫЕ ПРАВИЛА:
- Переводить в кг (вес) или м³ (объем)
- Учитывать насыпную плотность
- Примеры: песок, щебень, цемент, сухие смеси
            """
        }
        
        for name, template in specialized_prompts.items():
            prompt_template = PromptTemplate(
                name=f"specialized_{name}",
                type=PromptType.SPECIALIZED_PROMPT,
                template=template,
                variables=[],
                description=f"Specialized prompt for {name}"
            )
            self._templates[prompt_template.name] = prompt_template
    
    @property
    def service_name(self) -> str:
        """Get service name"""
        return self._service_name
    
    @property
    def version(self) -> str:
        """Get service version"""
        return self._version
    
    def get_system_prompt(self, common_units: List[str]) -> str:
        """
        Get system prompt for material parsing.
        
        Args:
            common_units: List of supported units
            
        Returns:
            str: System prompt
        """
        cache_key = f"system_prompt_{hash(tuple(common_units))}"
        
        # Check cache first
        if cache_key in self._prompt_cache:
            self.stats["cache_hits"] += 1
            return self._prompt_cache[cache_key]
        
        # Generate prompt
        template = self._templates.get("material_parsing_system")
        if not template:
            raise ValueError("System prompt template not found")
        
        # Render template
        units_text = ', '.join(common_units)
        prompt = template.render(common_units=units_text)
        
        # Cache result
        self._cache_prompt(cache_key, prompt)
        
        # Update statistics
        self.stats["total_prompts_generated"] += 1
        self.stats["cache_misses"] += 1
        template.usage_count += 1
        
        return prompt
    
    def get_user_prompt(
        self, 
        name: str, 
        unit: str, 
        material_hint: Optional[str] = None,
        is_block: bool = False
    ) -> str:
        """
        Get user prompt for specific material parsing.
        
        Args:
            name: Material name
            unit: Original unit
            material_hint: Unit hint for the material
            is_block: Whether material is a block material
            
        Returns:
            str: User prompt
        """
        cache_key = f"user_prompt_{hash((name, unit, material_hint, is_block))}"
        
        # Check cache first
        if cache_key in self._prompt_cache:
            self.stats["cache_hits"] += 1
            return self._prompt_cache[cache_key]
        
        # Generate prompt
        template = self._templates.get("material_parsing_user")
        if not template:
            raise ValueError("User prompt template not found")
        
        # Prepare variables
        hint_text = f"\\nПодсказка по материалу: {material_hint}" if material_hint else ""
        block_hint = "\\nВНИМАНИЕ: Это блочный материал - используй м3 (объем)!" if is_block else ""
        
        # Render template
        prompt = template.render(
            name=name,
            unit=unit,
            material_hint=hint_text,
            block_hint=block_hint
        )
        
        # Cache result
        self._cache_prompt(cache_key, prompt)
        
        # Update statistics
        self.stats["total_prompts_generated"] += 1
        self.stats["cache_misses"] += 1
        template.usage_count += 1
        
        return prompt
    
    def get_embeddings_prompt(self) -> str:
        """
        Get embeddings generation prompt.
        
        Returns:
            str: Embeddings prompt
        """
        cache_key = "embeddings_prompt"
        
        # Check cache first
        if cache_key in self._prompt_cache:
            self.stats["cache_hits"] += 1
            return self._prompt_cache[cache_key]
        
        # Generate prompt
        template = self._templates.get("embeddings_generation")
        if not template:
            raise ValueError("Embeddings prompt template not found")
        
        prompt = template.render()
        
        # Cache result
        self._cache_prompt(cache_key, prompt)
        
        # Update statistics
        self.stats["total_prompts_generated"] += 1
        self.stats["cache_misses"] += 1
        template.usage_count += 1
        
        return prompt
    
    def get_specialized_prompt(self, material_type: str) -> str:
        """
        Get specialized prompt for material type.
        
        Args:
            material_type: Type of material
            
        Returns:
            str: Specialized prompt
        """
        template_name = f"specialized_{material_type}"
        template = self._templates.get(template_name)
        
        if not template:
            self.logger.warning(f"Specialized prompt for '{material_type}' not found")
            return ""
        
        return template.render()
    
    async def optimize_prompt(
        self, 
        base_prompt: str, 
        context: Optional[PromptOptimizationContext] = None
    ) -> str:
        """
        Optimize prompt for better performance.
        
        Args:
            base_prompt: Base prompt to optimize
            context: Optimization context
            
        Returns:
            str: Optimized prompt
        """
        opt_context = context or self._default_context
        
        # Track optimization request
        self.stats["optimization_requests"] += 1
        
        # Simple optimization strategies
        optimized_prompt = base_prompt
        
        # Language-specific optimizations
        if opt_context.language == "russian":
            optimized_prompt = self._optimize_for_russian(optimized_prompt)
        
        # Domain-specific optimizations
        if opt_context.domain == "construction":
            optimized_prompt = self._optimize_for_construction(optimized_prompt)
        
        # Material-specific optimizations
        if opt_context.material_type:
            specialized = self.get_specialized_prompt(opt_context.material_type)
            if specialized:
                optimized_prompt = f"{optimized_prompt}\n\n{specialized}"
        
        # Confidence targeting
        if opt_context.target_confidence > 0.8:
            optimized_prompt = self._add_confidence_boosters(optimized_prompt)
        
        return optimized_prompt
    
    def _optimize_for_russian(self, prompt: str) -> str:
        """Optimize prompt for Russian language"""
        # Add Russian-specific instructions
        optimizations = [
            "Используй русские названия единиц измерения",
            "Учитывай склонения русских слов",
            "Обращай внимание на сокращения: м, кг, л, шт"
        ]
        
        optimization_text = "\n".join(f"- {opt}" for opt in optimizations)
        return f"{prompt}\n\nРУССКИЕ ОСОБЕННОСТИ:\n{optimization_text}"
    
    def _optimize_for_construction(self, prompt: str) -> str:
        """Optimize prompt for construction domain"""
        # Add construction-specific context
        construction_context = """
СТРОИТЕЛЬНЫЕ ОСОБЕННОСТИ:
- Учитывай стандартные размеры строительных материалов
- Обращай внимание на типовые упаковки (мешки, поддоны, пачки)
- Используй отраслевые сокращения и термины
"""
        return f"{prompt}\n\n{construction_context}"
    
    def _add_confidence_boosters(self, prompt: str) -> str:
        """Add confidence boosting instructions"""
        confidence_boosters = """
ПОВЫШЕНИЕ ТОЧНОСТИ:
- Внимательно анализируй каждое слово в названии
- Ищи явные указания на единицы измерения
- Используй контекст материала для принятия решений
- Будь консервативен в оценке confidence при сомнениях
"""
        return f"{prompt}\n\n{confidence_boosters}"
    
    def _cache_prompt(self, key: str, prompt: str) -> None:
        """Cache prompt with size limit"""
        if len(self._prompt_cache) >= self._cache_max_size:
            # Remove oldest entries (simple LRU)
            keys_to_remove = list(self._prompt_cache.keys())[:len(self._prompt_cache) // 2]
            for key_to_remove in keys_to_remove:
                del self._prompt_cache[key_to_remove]
        
        self._prompt_cache[key] = prompt
    
    def create_template(
        self, 
        name: str, 
        prompt_type: PromptType, 
        template: str,
        variables: List[str] = None,
        description: str = ""
    ) -> bool:
        """
        Create new prompt template.
        
        Args:
            name: Template name
            prompt_type: Type of prompt
            template: Template string
            variables: List of template variables
            description: Template description
            
        Returns:
            bool: True if successful
        """
        try:
            prompt_template = PromptTemplate(
                name=name,
                type=prompt_type,
                template=template,
                variables=variables or [],
                description=description
            )
            
            self._templates[name] = prompt_template
            self.stats["template_updates"] += 1
            
            self.logger.info(f"Created new template: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating template: {e}")
            return False
    
    def update_template(self, name: str, **updates) -> bool:
        """
        Update existing template.
        
        Args:
            name: Template name
            **updates: Updates to apply
            
        Returns:
            bool: True if successful
        """
        if name not in self._templates:
            self.logger.error(f"Template '{name}' not found")
            return False
        
        try:
            template = self._templates[name]
            
            for key, value in updates.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = time.time()
            self.stats["template_updates"] += 1
            
            # Clear cache to ensure new template is used
            self.clear_cache()
            
            self.logger.info(f"Updated template: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating template: {e}")
            return False
    
    def delete_template(self, name: str) -> bool:
        """
        Delete template.
        
        Args:
            name: Template name
            
        Returns:
            bool: True if successful
        """
        if name not in self._templates:
            self.logger.error(f"Template '{name}' not found")
            return False
        
        try:
            del self._templates[name]
            self.clear_cache()
            
            self.logger.info(f"Deleted template: {name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting template: {e}")
            return False
    
    def export_templates(self, output_path: Union[str, Path]) -> bool:
        """
        Export templates to file.
        
        Args:
            output_path: Output file path
            
        Returns:
            bool: True if successful
        """
        output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create export data
            export_data = {
                "metadata": {
                    "service_name": self.service_name,
                    "version": self.version,
                    "exported_at": time.time()
                },
                "templates": {
                    name: {
                        "name": template.name,
                        "type": template.type.value,
                        "template": template.template,
                        "variables": template.variables,
                        "description": template.description,
                        "version": template.version,
                        "usage_count": template.usage_count,
                        "success_rate": template.success_rate
                    }
                    for name, template in self._templates.items()
                }
            }
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Templates exported to: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting templates: {e}")
            return False
    
    def import_templates(self, input_path: Union[str, Path]) -> bool:
        """
        Import templates from file.
        
        Args:
            input_path: Input file path
            
        Returns:
            bool: True if successful
        """
        input_path = Path(input_path)
        
        try:
            # Check if file exists
            if not input_path.exists():
                self.logger.error(f"Templates file not found: {input_path}")
                return False
            
            # Load templates file
            with open(input_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            # Validate import data
            if "templates" not in import_data:
                self.logger.error("Invalid templates file format")
                return False
            
            # Import templates
            imported_count = 0
            for name, template_data in import_data["templates"].items():
                try:
                    template = PromptTemplate(
                        name=template_data["name"],
                        type=PromptType(template_data["type"]),
                        template=template_data["template"],
                        variables=template_data.get("variables", []),
                        description=template_data.get("description", ""),
                        version=template_data.get("version", "1.0.0"),
                        usage_count=template_data.get("usage_count", 0),
                        success_rate=template_data.get("success_rate", 0.0)
                    )
                    
                    self._templates[name] = template
                    imported_count += 1
                    
                except Exception as e:
                    self.logger.warning(f"Error importing template {name}: {e}")
            
            # Clear cache to ensure new templates are used
            self.clear_cache()
            
            self.logger.info(f"Imported {imported_count} templates")
            return imported_count > 0
            
        except Exception as e:
            self.logger.error(f"Error importing templates: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear prompt cache"""
        self._prompt_cache.clear()
        self.logger.info("Prompt cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get prompts manager statistics.
        
        Returns:
            Dict[str, Any]: Statistics dictionary
        """
        return {
            "service_name": self.service_name,
            "version": self.version,
            "total_templates": len(self._templates),
            "cache_size": len(self._prompt_cache),
            "cache_hit_rate": (
                self.stats["cache_hits"] / 
                (self.stats["cache_hits"] + self.stats["cache_misses"])
                if (self.stats["cache_hits"] + self.stats["cache_misses"]) > 0 else 0.0
            ),
            "template_usage": {
                name: {
                    "usage_count": template.usage_count,
                    "success_rate": template.success_rate
                }
                for name, template in self._templates.items()
            },
            "statistics": self.stats.copy()
        }
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get template information.
        
        Args:
            name: Template name
            
        Returns:
            Optional[Dict[str, Any]]: Template info or None if not found
        """
        template = self._templates.get(name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "type": template.type.value,
            "variables": template.variables,
            "description": template.description,
            "version": template.version,
            "usage_count": template.usage_count,
            "success_rate": template.success_rate,
            "created_at": template.created_at,
            "updated_at": template.updated_at
        }
    
    def list_templates(self) -> List[str]:
        """
        Get list of available templates.
        
        Returns:
            List[str]: List of template names
        """
        return list(self._templates.keys())


# Service factory
@lru_cache(maxsize=1)
def get_prompts_manager() -> SystemPromptsManager:
    """
    Get System Prompts Manager instance (singleton).
    
    Returns:
        SystemPromptsManager: Prompts manager instance
    """
    return SystemPromptsManager()


# Convenience functions
def get_material_parsing_system_prompt(common_units: List[str]) -> str:
    """
    Get system prompt for material parsing.
    
    Args:
        common_units: List of supported units
        
    Returns:
        str: System prompt
    """
    manager = get_prompts_manager()
    return manager.get_system_prompt(common_units)


def get_material_parsing_user_prompt(
    name: str, 
    unit: str, 
    material_hint: Optional[str] = None,
    is_block: bool = False
) -> str:
    """
    Get user prompt for material parsing.
    
    Args:
        name: Material name
        unit: Original unit
        material_hint: Material hint
        is_block: Whether material is a block
        
    Returns:
        str: User prompt
    """
    manager = get_prompts_manager()
    return manager.get_user_prompt(name, unit, material_hint, is_block) 