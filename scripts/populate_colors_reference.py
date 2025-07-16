"""
Script to populate the colors_reference collection with standard color names (RU/EN) and their embeddings.
"""

from core.database.collections.colors_reference import ColorsReferenceCollection
from core.database.collections.colors import ColorCollection
from services.combined_embedding_service import CombinedEmbeddingService
import asyncio

async def main():
    color_collection = ColorsReferenceCollection()
    embedding_service = CombinedEmbeddingService()
    for color_info in ColorCollection.BASE_COLORS:
        ru = color_info["name"]
        aliases = color_info["aliases"]
        # Use name and aliases for embedding text
        embedding_text = f"{ru} {' '.join(aliases)}"
        embedding = await embedding_service.get_color_embedding(embedding_text)
        await color_collection.save_color_reference(
            color_name=ru,
            aliases=aliases,
            embedding=embedding
        )
        print(f"Saved color: {ru} (aliases: {aliases})")

if __name__ == "__main__":
    asyncio.run(main()) 