"""
Script to populate the units_reference collection with standard unit names (RU/EN) and their embeddings.
"""

from core.database.collections.units_reference import UnitsReferenceCollection
from core.database.collections.units import UnitsCollection
from services.combined_embedding_service import CombinedEmbeddingService
import asyncio

async def main():
    unit_collection = UnitsReferenceCollection()
    embedding_service = CombinedEmbeddingService()
    for unit_info in UnitsCollection.BASE_UNITS:
        ru = unit_info["name"]
        aliases = unit_info["aliases"]
        embedding_text = f"{ru} {' '.join(aliases)}"
        embedding = await embedding_service.get_unit_embedding(embedding_text)
        await unit_collection.save_unit_reference(
            unit_name=ru,
            aliases=aliases,
            embedding=embedding
        )
        print(f"Saved unit: {ru} (aliases: {aliases})")

if __name__ == "__main__":
    asyncio.run(main()) 