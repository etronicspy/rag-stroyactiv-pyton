from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import pandas as pd
import io
import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.http import models
import numpy as np
import requests

# Load environment variables
load_dotenv('.env.local')

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize Qdrant client
QDRANT_URL = "https://8e8c931b-9a49-478d-9a45-284600e6fa1d.europe-west3-0.gcp.cloud.qdrant.io"
COLLECTION_NAME = "products"

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=os.getenv("QDRANT_API_KEY")  # API ключ будет взят из .env.local
)

# Initialize FastAPI app
app = FastAPI(title="Price List Processor API")

class PriceItem(BaseModel):
    """Модель для элемента прайс-листа"""
    name: str = Field(description="Название товара/услуги")
    price: float = Field(description="Цена")

class PriceResponse(BaseModel):
    """Модель ответа API"""
    items: List[PriceItem] = Field(description="Список обработанных позиций")
    total_items: int = Field(description="Общее количество позиций")
    original_columns: List[str] = Field(description="Исходные названия колонок")
    vectors_saved: int = Field(description="Количество сохраненных векторов", default=0)

async def create_embeddings(texts: List[str]) -> List[List[float]]:
    """Создает эмбеддинги для списка текстов"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [embedding.embedding for embedding in response.data]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create embeddings: {str(e)}")

async def ensure_collection_exists():
    """Проверяет существование коллекции и создает её при необходимости"""
    try:
        collections = qdrant_client.get_collections().collections
        exists = any(collection.name == COLLECTION_NAME for collection in collections)
        
        if not exists:
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=models.VectorParams(
                    size=1536,  # Размерность для text-embedding-3-small
                    distance=models.Distance.COSINE
                )
            )
            print(f"Collection {COLLECTION_NAME} created successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ensure collection exists: {str(e)}")

async def save_to_qdrant(items: List[PriceItem]) -> int:
    """Сохраняет товары в Qdrant"""
    try:
        # Убеждаемся, что коллекция существует
        await ensure_collection_exists()
        
        # Получаем названия товаров
        names = [item.name for item in items]
        
        # Создаем эмбеддинги
        embeddings = await create_embeddings(names)
        
        # Подготавливаем points для сохранения
        points = []
        for i, (embedding, item) in enumerate(zip(embeddings, items)):
            points.append(models.PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "name": item.name,
                    "price": item.price
                }
            ))
        
        # Сохраняем в Qdrant
        operation_info = qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=points
        )
        
        return len(points)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save to Qdrant: {str(e)}")

async def analyze_columns(df: pd.DataFrame) -> dict:
    """Анализирует колонки таблицы с помощью GPT для определения name и price"""
    columns = df.columns.tolist()
    
    # Формируем промпт для GPT
    prompt = f"""Analyze these column names and identify which columns represent 'name' and 'price':
Columns: {columns}

Return only a JSON object with two fields:
1. 'name_column': the column name that represents item names
2. 'price_column': the column name that represents prices

Example response:
{{"name_column": "Product Name", "price_column": "Cost"}}"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a data analysis assistant. Respond only with the requested JSON format."},
            {"role": "user", "content": prompt}
        ]
    )
    
    # Парсим JSON из ответа
    try:
        return json.loads(response.choices[0].message.content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse GPT response")

@app.post("/process_price", response_model=PriceResponse)
async def process_price(file: UploadFile = File(...)):
    """
    Обрабатывает загруженный прайс-лист, создает эмбеддинги и сохраняет в Qdrant.
    
    Поддерживаемые форматы:
    - Excel (.xlsx, .xls)
    - CSV (.csv)
    """
    try:
        # Читаем файл в зависимости от формата
        content = await file.read()
        if file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(content))
        elif file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Please upload .xlsx, .xls, or .csv file")

        # Анализируем колонки с помощью GPT
        columns = await analyze_columns(df)
        name_col = columns['name_column']
        price_col = columns['price_column']

        # Преобразуем данные в нужный формат
        items = []
        for _, row in df.iterrows():
            try:
                # Очищаем цену от нечисловых символов и конвертируем в float
                price_str = str(row[price_col]).replace(',', '.').replace(' ', '')
                price = float(''.join(c for c in price_str if c.isdigit() or c == '.'))
                
                items.append(PriceItem(
                    name=str(row[name_col]).strip(),
                    price=price
                ))
            except (ValueError, TypeError):
                continue  # Пропускаем строки с некорректными данными

        # Сохраняем в Qdrant
        vectors_saved = await save_to_qdrant(items)

        return PriceResponse(
            items=items,
            total_items=len(items),
            original_columns=df.columns.tolist(),
            vectors_saved=vectors_saved
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка состояния сервера и подключения к Qdrant"""
    try:
        # Проверяем подключение к Qdrant
        collections = qdrant_client.get_collections().collections
        qdrant_status = "connected"
    except:
        qdrant_status = "disconnected"

    return {
        "status": "ok",
        "supported_formats": [".xlsx", ".xls", ".csv"],
        "qdrant_status": qdrant_status
    }

@app.get("/vectors/count")
async def get_vectors_count():
    """Возвращает количество векторов в коллекции"""
    try:
        # Используем прямой REST API запрос с API ключом
        headers = {"api-key": os.getenv("QDRANT_API_KEY")}
        response = requests.get(f"{QDRANT_URL}/collections/{COLLECTION_NAME}", headers=headers)
        
        if response.status_code == 200:
            collection_info = response.json()
            points_count = collection_info.get("result", {}).get("points_count", 0)
            return {
                "collection_name": COLLECTION_NAME,
                "vectors_count": points_count,
                "status": "ok",
                "message": f"Collection found with {points_count} points"
            }
        elif response.status_code == 404:
            return {
                "collection_name": COLLECTION_NAME,
                "vectors_count": 0,
                "status": "not_found",
                "message": "Collection does not exist"
            }
        else:
            return {
                "collection_name": COLLECTION_NAME,
                "vectors_count": 0,
                "status": "error",
                "message": f"Failed to get collection info: {response.text}"
            }
    except Exception as e:
        return {
            "collection_name": COLLECTION_NAME,
            "vectors_count": 0,
            "status": "error",
            "error": str(e)
        }

@app.get("/vectors/data")
async def get_vectors_data():
    """Возвращает данные сохраненных векторов"""
    try:
        # Получаем все точки из коллекции
        points = qdrant_client.scroll(
            collection_name=COLLECTION_NAME,
            limit=100,  # ограничиваем количество результатов
            with_payload=True,  # включаем payload
            with_vectors=False  # не включаем сами векторы, так как они большие
        )[0]
        
        return {
            "collection_name": COLLECTION_NAME,
            "total_points": len(points),
            "points": [
                {
                    "id": point.id,
                    "payload": point.payload
                }
                for point in points
            ]
        }
    except Exception as e:
        return {
            "collection_name": COLLECTION_NAME,
            "total_points": 0,
            "points": [],
            "error": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))  # Изменим порт по умолчанию на 8001
    print(f"Starting server on port {port}")
    uvicorn.run(
        "price_processor:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["./"]
    ) 