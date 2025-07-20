"""
Populate script for construction_colors collection in Qdrant.

This script generates color data with embeddings and uploads them to the construction_colors collection
using the current ColorCollection schema and DatabaseFallbackManager.
"""
import asyncio

from core.database.collections.colors import ColorCollection
from core.database.factories import get_fallback_manager
from core.logging import get_logger

logger = get_logger(__name__)

async def main():
    print("=== Starting populate script for construction_colors ===")
    logger.info("Starting populate script for construction_colors...")
    
    print("Getting fallback manager...")
    fallback_manager = get_fallback_manager()
    print("Fallback manager created successfully")
    
    collection_config = ColorCollection.get_collection_config()
    collection_name = collection_config["collection_name"]
    print(f"Collection name: {collection_name}")

    # 1. Create collection if not exists
    print("Checking if collection exists...")
    exists = await fallback_manager.collection_exists(collection_name)
    print(f"Collection exists: {exists}")
    
    if not exists:
        print("Creating collection...")
        await fallback_manager.create_collection(collection_config)
        print(f"Created collection: {collection_name}")
        logger.info(f"Created collection: {collection_name}")
    else:
        print(f"Collection already exists: {collection_name}")
        logger.info(f"Collection already exists: {collection_name}")

    # 2. Generate color data (embeddings are zeros by default)
    print("Generating color data...")
    color_data = ColorCollection.generate_color_data()
    print(f"Generated {len(color_data)} color records for population.")
    logger.info(f"Generated {len(color_data)} color records for population.")

    # 3. Insert in batches
    print("Inserting data in batches...")
    batch_size = 50
    total_inserted = 0
    for i in range(0, len(color_data), batch_size):
        batch = color_data[i:i+batch_size]
        print(f"Inserting batch {i//batch_size+1} with {len(batch)} colors...")
        await fallback_manager.insert_batch(collection_name, batch)
        total_inserted += len(batch)
        print(f"Inserted batch {i//batch_size+1}: {len(batch)} colors (total: {total_inserted})")
        logger.info(f"Inserted batch {i//batch_size+1}: {len(batch)} colors (total: {total_inserted})")

    print(f"Successfully populated {collection_name} with {total_inserted} colors.")
    logger.info(f"Successfully populated {collection_name} with {total_inserted} colors.")

if __name__ == "__main__":
    asyncio.run(main()) 