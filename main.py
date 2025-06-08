from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter

# Load environment variables from env.local
load_dotenv('env.local')

# Initialize FastAPI app
app = FastAPI(title="RAG Search API")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Qdrant client
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
            collection_name="your_collection_name",  # Replace with your collection name
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 