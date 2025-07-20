"""
Populate script for construction_units collection in Qdrant.

This script generates unit data with embeddings and uploads them to the construction_units collection
using the current UnitsCollection schema and DatabaseFallbackManager.
"""
import asyncio

from core.database.collections.units import UnitsCollection
from core.database.factories import get_fallback_manager
from core.logging import get_logger

logger = get_logger(__name__)

async def main():
    logger.info("Starting populate script for construction_units...")
    fallback_manager = get_fallback_manager()
    collection_config = UnitsCollection.get_collection_config()
    collection_name = collection_config["collection_name"]

    # 1. Create collection if not exists
    exists = await fallback_manager.collection_exists(collection_name)
    if not exists:
        await fallback_manager.create_collection(collection_config)
        logger.info(f"Created collection: {collection_name}")
    else:
        logger.info(f"Collection already exists: {collection_name}")

    # 2. Generate unit data (embeddings are zeros by default)
    unit_data = UnitsCollection.generate_units_data()
    logger.info(f"Generated {len(unit_data)} unit records for population.")

    # 3. Insert in batches
    batch_size = 50
    total_inserted = 0
    for i in range(0, len(unit_data), batch_size):
        batch = unit_data[i:i+batch_size]
        await fallback_manager.insert_batch(collection_name, batch)
        total_inserted += len(batch)
        logger.info(f"Inserted batch {i//batch_size+1}: {len(batch)} units (total: {total_inserted})")

    logger.info(f"Successfully populated {collection_name} with {total_inserted} units.")

if __name__ == "__main__":
    asyncio.run(main()) 