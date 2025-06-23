"""Database seed data module.

Модуль для заполнения БД начальными данными.
Содержит базовые категории материалов и единицы измерения.
"""

from typing import Dict
from core.logging import get_logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = get_logger(__name__)


# Seed data for categories
SEED_CATEGORIES = [
    {
        "name": "Строительные материалы",
        "description": "Основные строительные материалы",
        "parent_id": None,
        "children": [
            {"name": "Кирпич", "description": "Кирпичные изделия всех типов"},
            {"name": "Бетон", "description": "Бетонные смеси и растворы"},
            {"name": "Арматура", "description": "Металлическая арматура"},
            {"name": "Цемент", "description": "Цементные смеси и порошки"},
        ]
    },
    {
        "name": "Отделочные материалы",
        "description": "Материалы для внутренней и внешней отделки",
        "parent_id": None,
        "children": [
            {"name": "Краски", "description": "Лакокрасочные материалы"},
            {"name": "Обои", "description": "Обои всех типов"},
            {"name": "Плитка", "description": "Керамическая и другие виды плитки"},
        ]
    },
    {
        "name": "Инструменты",
        "description": "Строительные инструменты и оборудование",
        "parent_id": None,
        "children": [
            {"name": "Ручные инструменты", "description": "Инструменты ручного труда"},
            {"name": "Электроинструменты", "description": "Электрические инструменты"},
        ]
    },
    {
        "name": "Сантехника",
        "description": "Сантехнические материалы и оборудование",
        "parent_id": None,
        "children": [
            {"name": "Трубы", "description": "Трубы различных типов"},
            {"name": "Фитинги", "description": "Соединительные элементы"},
        ]
    },
    {
        "name": "Электрика",
        "description": "Электротехнические материалы",
        "parent_id": None,
        "children": [
            {"name": "Кабели", "description": "Электрические кабели"},
            {"name": "Выключатели", "description": "Выключатели и розетки"},
        ]
    }
]

# Seed data for units
SEED_UNITS = [
    # Weight units
    {"name": "килограмм", "symbol": "кг", "unit_type": "weight", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "грамм", "symbol": "г", "unit_type": "weight", "base_unit_id": 1, "conversion_factor": 0.001},
    {"name": "тонна", "symbol": "т", "unit_type": "weight", "base_unit_id": 1, "conversion_factor": 1000.0},
    
    # Volume units
    {"name": "литр", "symbol": "л", "unit_type": "volume", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "миллилитр", "symbol": "мл", "unit_type": "volume", "base_unit_id": 4, "conversion_factor": 0.001},
    {"name": "кубический метр", "symbol": "м³", "unit_type": "volume", "base_unit_id": 4, "conversion_factor": 1000.0},
    
    # Length units
    {"name": "метр", "symbol": "м", "unit_type": "length", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "сантиметр", "symbol": "см", "unit_type": "length", "base_unit_id": 7, "conversion_factor": 0.01},
    {"name": "миллиметр", "symbol": "мм", "unit_type": "length", "base_unit_id": 7, "conversion_factor": 0.001},
    {"name": "километр", "symbol": "км", "unit_type": "length", "base_unit_id": 7, "conversion_factor": 1000.0},
    
    # Area units
    {"name": "квадратный метр", "symbol": "м²", "unit_type": "area", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "квадратный сантиметр", "symbol": "см²", "unit_type": "area", "base_unit_id": 11, "conversion_factor": 0.0001},
    
    # Count units
    {"name": "штука", "symbol": "шт", "unit_type": "count", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "упаковка", "symbol": "упак", "unit_type": "count", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "коробка", "symbol": "кор", "unit_type": "count", "base_unit_id": None, "conversion_factor": 1.0},
    {"name": "мешок", "symbol": "меш", "unit_type": "count", "base_unit_id": None, "conversion_factor": 1.0},
    
    # Specific construction units
    {"name": "погонный метр", "symbol": "пог.м", "unit_type": "length", "base_unit_id": 7, "conversion_factor": 1.0},
    {"name": "квадратный дециметр", "symbol": "дм²", "unit_type": "area", "base_unit_id": 11, "conversion_factor": 0.01},
]


class DatabaseSeeder:
    """Database seeder for initializing reference data.
    
    Класс для инициализации справочных данных в БД.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize seeder with database session.
        
        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
    
    async def seed_categories(self) -> None:
        """Seed categories data.
        
        Создает базовые категории материалов с иерархической структурой.
        """
        logger.info("Seeding categories data...")
        
        try:
            # Check if categories already exist
            result = await self.session.execute(text("SELECT COUNT(*) FROM categories"))
            count = result.scalar()
            
            if count > 0:
                logger.info(f"Categories already exist ({count} records), skipping seed")
                return
            
            # Insert parent categories first
            parent_ids = {}
            
            for category_group in SEED_CATEGORIES:
                # Insert parent category
                parent_result = await self.session.execute(
                    text("""
                        INSERT INTO categories (name, description, parent_id, is_active)
                        VALUES (:name, :description, :parent_id, true)
                        RETURNING id
                    """),
                    {
                        "name": category_group["name"],
                        "description": category_group["description"],
                        "parent_id": category_group["parent_id"]
                    }
                )
                parent_id = parent_result.scalar()
                parent_ids[category_group["name"]] = parent_id
                
                # Insert child categories
                for child in category_group.get("children", []):
                    await self.session.execute(
                        text("""
                            INSERT INTO categories (name, description, parent_id, is_active)
                            VALUES (:name, :description, :parent_id, true)
                        """),
                        {
                            "name": child["name"],
                            "description": child["description"],
                            "parent_id": parent_id
                        }
                    )
            
            await self.session.commit()
            logger.info(f"Successfully seeded {len(SEED_CATEGORIES)} parent categories")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to seed categories: {e}")
            raise
    
    async def seed_units(self) -> None:
        """Seed units data.
        
        Создает базовые единицы измерения с поддержкой конвертации.
        """
        logger.info("Seeding units data...")
        
        try:
            # Check if units already exist
            result = await self.session.execute(text("SELECT COUNT(*) FROM units"))
            count = result.scalar()
            
            if count > 0:
                logger.info(f"Units already exist ({count} records), skipping seed")
                return
            
            # Insert units (base units first, then dependent ones)
            unit_ids = {}
            
            # First pass: insert base units (no base_unit_id)
            for unit in SEED_UNITS:
                if unit["base_unit_id"] is None:
                    result = await self.session.execute(
                        text("""
                            INSERT INTO units (name, symbol, unit_type, base_unit_id, conversion_factor, is_active)
                            VALUES (:name, :symbol, :unit_type, :base_unit_id, :conversion_factor, true)
                            RETURNING id
                        """),
                        unit
                    )
                    unit_id = result.scalar()
                    unit_ids[unit["name"]] = unit_id
            
            # Second pass: update base_unit_id references and insert dependent units
            for i, unit in enumerate(SEED_UNITS):
                if unit["base_unit_id"] is not None:
                    # Map original base_unit_id to actual database id
                    base_unit_original_index = unit["base_unit_id"] - 1  # Convert to 0-based index
                    base_unit_name = SEED_UNITS[base_unit_original_index]["name"]
                    actual_base_unit_id = unit_ids.get(base_unit_name)
                    
                    if actual_base_unit_id:
                        await self.session.execute(
                            text("""
                                INSERT INTO units (name, symbol, unit_type, base_unit_id, conversion_factor, is_active)
                                VALUES (:name, :symbol, :unit_type, :base_unit_id, :conversion_factor, true)
                            """),
                            {
                                "name": unit["name"],
                                "symbol": unit["symbol"],
                                "unit_type": unit["unit_type"],
                                "base_unit_id": actual_base_unit_id,
                                "conversion_factor": unit["conversion_factor"]
                            }
                        )
            
            await self.session.commit()
            logger.info(f"Successfully seeded {len(SEED_UNITS)} units")
            
        except Exception as e:
            await self.session.rollback()
            logger.error(f"Failed to seed units: {e}")
            raise
    
    async def seed_all(self) -> None:
        """Seed all reference data.
        
        Инициализирует все справочные данные в правильном порядке.
        """
        logger.info("Starting database seeding...")
        
        try:
            await self.seed_categories()
            await self.seed_units()
            logger.info("Database seeding completed successfully")
            
        except Exception as e:
            logger.error(f"Database seeding failed: {e}")
            raise
    
    async def verify_seed_data(self) -> Dict[str, int]:
        """Verify that seed data was created successfully.
        
        Returns:
            Dict with counts of created records
        """
        try:
            categories_result = await self.session.execute(text("SELECT COUNT(*) FROM categories"))
            units_result = await self.session.execute(text("SELECT COUNT(*) FROM units"))
            
            return {
                "categories": categories_result.scalar(),
                "units": units_result.scalar()
            }
            
        except Exception as e:
            logger.error(f"Failed to verify seed data: {e}")
            raise


async def seed_database(session: AsyncSession) -> Dict[str, int]:
    """Convenience function to seed database.
    
    Args:
        session: Async SQLAlchemy session
        
    Returns:
        Dictionary with counts of seeded records
    """
    seeder = DatabaseSeeder(session)
    await seeder.seed_all()
    return await seeder.verify_seed_data() 