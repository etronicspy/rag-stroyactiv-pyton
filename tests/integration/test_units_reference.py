import pytest
import asyncio
from core.database.collections.units_reference import UnitsReferenceCollection
from services.combined_embedding_service import CombinedEmbeddingService

@pytest.mark.asyncio
async def test_unit_embedding_search_ru_en():
    unit_collection = UnitsReferenceCollection()
    embedding_service = CombinedEmbeddingService()

    # RU вариант
    ru_query = "кг"
    ru_embedding = await embedding_service.get_unit_embedding(ru_query)
    ru_result = await unit_collection.search_by_embedding(ru_embedding)
    assert ru_result is not None, "Should find unit for RU embedding"
    assert ru_result.unit_name.lower() == "кг" or ru_result.unit_name_en.lower() == "kilogram"

    # EN вариант
    en_query = "kilogram"
    en_embedding = await embedding_service.get_unit_embedding(en_query)
    en_result = await unit_collection.search_by_embedding(en_embedding)
    assert en_result is not None, "Should find unit for EN embedding"
    assert en_result.unit_name.lower() == "кг" or en_result.unit_name_en.lower() == "kilogram" 