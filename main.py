from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter

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
        def create(self, **kwargs):
            class MockResponse:
                class MockData:
                    embedding = [0.1] * 1536
                data = [MockData()]
            return MockResponse()

    class MockOpenAI:
        embeddings = MockEmbeddings()
    
    class MockQdrant:
        def search(self, **kwargs):
            return [
                type('obj', (object,), {
                    'score': 0.95,
                    'payload': {
                        'text': 'Это тестовый ответ для демонстрации работы API',
                        'source': 'https://test-source.com/article1'
                    }
                }),
                type('obj', (object,), {
                    'score': 0.85,
                    'payload': {
                        'text': 'Второй тестовый ответ для демонстрации',
                        'source': 'https://test-source.com/article2'
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

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

class SearchResult(BaseModel):
    query: str
    matches: List[dict]
    sources: List[str]

@app.post("/search", response_model=SearchResult)
async def search(search_query: SearchQuery):
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
        matches = []
        sources = []
        for result in search_results:
            matches.append({
                "score": result.score,
                "payload": result.payload
            })
            if "source" in result.payload:
                sources.append(result.payload["source"])

        return SearchResult(
            query=search_query.query,
            matches=matches,
            sources=list(set(sources))  # Remove duplicates
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add health check endpoint
@app.get("/health")
async def health_check():
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