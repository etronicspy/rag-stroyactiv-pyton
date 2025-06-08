"""
FastAPI приложение для семантического поиска с использованием RAG (Retrieval-Augmented Generation).
Поддерживает тестовый и production режимы работы, интегрируется с OpenAI для эмбеддингов
и Qdrant для векторного поиска.
"""

import os
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient

# Load environment variables from .env.local
load_dotenv('.env.local')

# Initialize FastAPI app
app = FastAPI(title="RAG Search API")

# Check if we're in test mode
TEST_MODE = os.getenv("TEST_MODE", "true").lower() == "true"

# Get collection name from environment
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "default_collection")

if TEST_MODE:
    print("Running in TEST MODE - using mock responses")
    # Mock clients for testing
    class MockEmbeddings:
        """Мок-класс для эмуляции сервиса эмбеддингов"""
        def create(self, **kwargs):
            """Создает мок-эмбеддинг фиксированной длины"""
            class MockResponse:
                """Мок-класс для эмуляции ответа от сервиса эмбеддингов"""
                class MockData:
                    """Мок-класс для эмуляции данных эмбеддинга"""
                    embedding = [0.1] * 1536
                data = [MockData()]
            return MockResponse()

    class MockOpenAI:
        """Мок-класс для эмуляции клиента OpenAI"""
        embeddings = MockEmbeddings()

    class MockQdrant:
        """Мок-класс для эмуляции клиента Qdrant"""
        def search(self, **kwargs):
            """Возвращает фиксированный набор тестовых результатов"""
            return [
                type('obj', (object,), {
                    'score': 0.95,
                    'payload': {
                        'content': 'Это тестовый ответ для демонстрации работы API'
                    }
                }),
                type('obj', (object,), {
                    'score': 0.85,
                    'payload': {
                        'content': 'Второй тестовый ответ для демонстрации'
                    }
                })
            ]

    client = MockOpenAI()
    qdrant_client = MockQdrant()
else:
    # Initialize real clients
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    qdrant_client = QdrantClient(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

class SearchResult(BaseModel):
    """Модель для одного результата поиска"""
    score: float = Field(description="Оценка релевантности результата")
    content: str = Field(description="Текстовое содержание результата")

class SearchQuery(BaseModel):
    """Модель для поискового запроса"""
    query: str = Field(description="Поисковый запрос")
    limit: Optional[int] = Field(default=5, description="Максимальное количество результатов")
    min_score: Optional[float] = Field(default=0.0, description="Минимальный порог релевантности")

class SearchResponse(BaseModel):
    """Модель ответа API"""
    query: str = Field(description="Исходный поисковый запрос")
    results: List[SearchResult] = Field(description="Список найденных результатов")
    total_found: int = Field(description="Общее количество найденных результатов")

@app.post("/search", response_model=SearchResponse)
async def search(search_query: SearchQuery):
    """
    Поиск релевантной информации по запросу.
    
    - Преобразует текстовый запрос в эмбеддинг
    - Ищет похожие документы в Qdrant
    - Возвращает отсортированный по релевантности список результатов
    """
    try:
        # Get embeddings for the search query
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=search_query.query
        )
        query_vector = response.data[0].embedding

        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            limit=search_query.limit
        )

        # Process results
        results = []
        for result in search_results:
            if result.score >= search_query.min_score:
                results.append(SearchResult(
                    score=result.score,
                    content=result.payload.get("content", "")
                ))

        return SearchResponse(
            query=search_query.query,
            results=results,
            total_found=len(results)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

@app.get("/health")
async def health_check():
    """Проверка состояния сервера"""
    return {
        "status": "ok",
        "mode": "test" if TEST_MODE else "production",
        "collection": COLLECTION_NAME
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting server in {'TEST' if TEST_MODE else 'PRODUCTION'} mode")
    print(f"Using collection: {COLLECTION_NAME}")
    uvicorn.run(app, host="0.0.0.0", port=port) 
