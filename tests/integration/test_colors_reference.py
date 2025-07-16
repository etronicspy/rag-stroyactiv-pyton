import pytest
import asyncio
from core.database.collections.colors_reference import ColorsReferenceCollection
from services.combined_embedding_service import CombinedEmbeddingService

@pytest.mark.asyncio
async def test_color_embedding_search_ru_en():
    color_collection = ColorsReferenceCollection()
    embedding_service = CombinedEmbeddingService()

    # RU вариант
    ru_query = "желтый"
    ru_embedding = await embedding_service.get_color_embedding(ru_query)
    ru_result = await color_collection.search_by_embedding(ru_embedding)
    assert ru_result is not None, "Should find color for RU embedding"
    assert ru_result.color_name.lower() == "желтый" or ru_result.color_name_en.lower() == "yellow"

    # EN вариант
    en_query = "yellow"
    en_embedding = await embedding_service.get_color_embedding(en_query)
    en_result = await color_collection.search_by_embedding(en_embedding)
    assert en_result is not None, "Should find color for EN embedding"
    assert en_result.color_name.lower() == "желтый" or en_result.color_name_en.lower() == "yellow" 