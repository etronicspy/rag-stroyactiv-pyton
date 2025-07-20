"""
Populate script for construction_categories collection in Qdrant.

This script generates category data with embeddings and uploads them to the construction_categories collection.
"""
import asyncio
import uuid
from datetime import datetime

from core.database.factories import get_fallback_manager
from core.logging import get_logger

logger = get_logger(__name__)

CATEGORIES = [
    {
        "name": "Кирпич",
        "aliases": ["кирпич", "brick", "кирпич керамический"],
        "description": "Строительный материал для возведения стен"
    },
    {
        "name": "Бетон",
        "aliases": ["бетон", "concrete", "бетонный раствор"],
        "description": "Смесь для монолитных и сборных конструкций"
    },
    {
        "name": "Доска",
        "aliases": ["доска", "board", "пиломатериал"],
        "description": "Пиломатериал для строительства и отделки"
    }
]

VECTOR_SIZE = 1536
COLLECTION_NAME = "construction_categories"

async def main():
    logger.info("Starting populate script for construction_categories...")
    fallback_manager = get_fallback_manager()
    collection_config = {
        "collection_name": COLLECTION_NAME,
        "vector_size": VECTOR_SIZE,
        "distance": "Cosine",
        "on_disk_payload": True
    }

    # 1. Create collection if not exists
    exists = await fallback_manager.collection_exists(COLLECTION_NAME)
    if not exists:
        await fallback_manager.create_collection(collection_config)
        logger.info(f"Created collection: {COLLECTION_NAME}")
    else:
        logger.info(f"Collection already exists: {COLLECTION_NAME}")

    # 2. Generate category data (embeddings are zeros by default)
    current_time = datetime.utcnow().isoformat()
    category_data = []
    for cat in CATEGORIES:
        category_data.append({
            "id": str(uuid.uuid4()),
            "vector": [0.0] * VECTOR_SIZE,
            "payload": {
                "name": cat["name"],
                "aliases": cat["aliases"],
                "description": cat["description"],
                "created_at": current_time,
                "updated_at": current_time
            }
        })
    logger.info(f"Generated {len(category_data)} category records for population.")

    # 3. Insert all at once (small set)
    await fallback_manager.insert_batch(COLLECTION_NAME, category_data)
    logger.info(f"Successfully populated {COLLECTION_NAME} with {len(category_data)} categories.")

if __name__ == "__main__":
    asyncio.run(main()) 