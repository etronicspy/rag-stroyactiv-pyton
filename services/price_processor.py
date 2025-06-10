from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
from core.models.materials import Material, Category, Unit
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
import uuid
import logging
import numpy as np
from core.config import settings, get_vector_db_client, get_ai_client
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = logging.getLogger(__name__)

class PriceProcessor:
    def __init__(self):
        # Use centralized client factories
        self.qdrant_client = get_vector_db_client()
        self.ai_client = get_ai_client()
        
        # Get configuration
        self.db_config = settings.get_vector_db_config()
        
        self.required_columns = ["name", "category", "unit", "price"]
        self.optional_columns = ["description"]
        
    def _validate_columns(self, df: pd.DataFrame) -> None:
        """Validate that all required columns are present"""
        missing_columns = [col for col in self.required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
    
    def _validate_data(self, df: pd.DataFrame) -> None:
        """Validate data types and values"""
        # Check for empty values in required columns
        for col in self.required_columns:
            if df[col].isnull().any():
                raise ValueError(f"Column {col} contains empty values")
        
        # Validate price is numeric and positive
        if not pd.to_numeric(df["price"], errors="coerce").notnull().all():
            raise ValueError("Price column contains non-numeric values")
        if (df["price"] <= 0).any():
            raise ValueError("Price column contains zero or negative values")
    
    def _prepare_points(self, df: pd.DataFrame, date: str) -> List[models.PointStruct]:
        """Prepare points for Qdrant insertion"""
        points = []
        for _, row in df.iterrows():
            point_id = str(uuid.uuid4())
            payload = {
                "id": point_id,
                "name": row["name"],
                "category": row["category"],
                "unit": row["unit"],
                "price": float(row["price"]),
                "date": date
            }
            if "description" in row and pd.notna(row["description"]):
                payload["description"] = row["description"]
            
            # Create a simple vector representation
            vector = np.zeros(1536)  # Using a zero vector for now
            
            points.append(models.PointStruct(
                id=point_id,
                vector=vector.tolist(),
                payload=payload
            ))
        return points
    
    def _get_collection_name(self, supplier_id: str) -> str:
        """Generate collection name for supplier"""
        return f"supplier_{supplier_id}_prices"
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using configured AI provider"""
        try:
            if settings.AI_PROVIDER.value == "openai":
                ai_config = settings.get_ai_config()
                # For text-embedding-3-small, specify dimensions to get 1536-dimensional vectors
                if "text-embedding-3" in ai_config["model"]:
                    response = await self.ai_client.embeddings.create(
                        input=text,
                        model=ai_config["model"],
                        dimensions=1536
                    )
                else:
                    response = await self.ai_client.embeddings.create(
                        input=text,
                        model=ai_config["model"]
                    )
                return response.data[0].embedding
            elif settings.AI_PROVIDER.value == "huggingface":
                # For HuggingFace, client is SentenceTransformer
                embedding = self.ai_client.encode([text])
                return embedding[0].tolist()
            else:
                raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise
    
    def _ensure_collection_exists(self, collection_name: str):
        """Ensure the supplier collection exists"""
        try:
            collections = self.qdrant_client.get_collections()
            if not any(c.name == collection_name for c in collections.collections):
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=self.db_config["vector_size"], 
                        distance=Distance.COSINE
                    ),
                )
                logger.info(f"Created collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection exists: {e}")
            raise

    def validate_file_format(self, file_path: str, content_type: str = None) -> bool:
        """Validate if file is CSV or Excel"""
        if file_path.lower().endswith(('.csv', '.xlsx', '.xls')):
            return True
        if content_type and any(ct in content_type.lower() for ct in ['csv', 'excel', 'spreadsheet']):
            return True
        return False

    def read_price_file(self, file_path: str) -> pd.DataFrame:
        """Read price file (CSV or Excel) and return DataFrame"""
        try:
            if file_path.lower().endswith('.csv'):
                # Try different encodings for CSV
                encodings = ['utf-8', 'cp1251', 'latin1']
                for encoding in encodings:
                    try:
                        df = pd.read_csv(file_path, encoding=encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError("Could not read CSV file with any encoding")
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                raise ValueError("Unsupported file format")
            
            return df
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise

    def validate_required_columns(self, df: pd.DataFrame) -> List[str]:
        """Validate that DataFrame has required columns"""
        required_columns = ['name', 'category', 'unit', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        return missing_columns

    def clean_price_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate price data"""
        try:
            # Remove rows with empty names
            df = df.dropna(subset=['name'])
            
            # Clean price column - remove non-numeric characters and convert to float
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
                # Remove rows with invalid prices
                df = df.dropna(subset=['price'])
                # Remove negative prices
                df = df[df['price'] >= 0]
            
            # Fill missing descriptions
            if 'description' not in df.columns:
                df['description'] = ''
            else:
                df['description'] = df['description'].fillna('')
            
            # Clean text columns
            text_columns = ['name', 'category', 'unit', 'description']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            return df
        except Exception as e:
            logger.error(f"Error cleaning price data: {e}")
            raise

    async def process_price_list(self, file_path: str, supplier_id: str) -> Dict[str, Any]:
        """Process price list file and store in vector database"""
        try:
            # Read and validate file
            df = self.read_price_file(file_path)
            
            # Validate required columns
            missing_columns = self.validate_required_columns(df)
            if missing_columns:
                raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
            
            # Clean data
            df = self.clean_price_data(df)
            
            if df.empty:
                raise ValueError("No valid data found after cleaning")
            
            # Prepare collection
            collection_name = self._get_collection_name(supplier_id)
            self._ensure_collection_exists(collection_name)
            
            # Process materials and create embeddings
            points = []
            current_date = datetime.utcnow().isoformat()
            
            for _, row in df.iterrows():
                try:
                    # Create text for embedding
                    text_for_embedding = f"{row['name']} {row['category']} {row.get('description', '')}"
                    embedding = await self._get_embedding(text_for_embedding)
                    
                    # Create point
                    point_id = str(uuid.uuid4())
                    point = PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "name": row['name'],
                            "category": row['category'],
                            "unit": row['unit'],
                            "price": float(row['price']),
                            "description": row.get('description', ''),
                            "supplier_id": supplier_id,
                            "upload_date": current_date,
                        }
                    )
                    points.append(point)
                    
                except Exception as e:
                    logger.warning(f"Error processing row {row.get('name', 'unknown')}: {e}")
                    continue
            
            if not points:
                raise ValueError("No valid points created from data")
            
            # Store in Qdrant
            self.qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            
            # Enforce limit of 3 price lists per supplier
            self._enforce_price_list_limit(collection_name)
            
            logger.info(f"Successfully processed {len(points)} materials for supplier {supplier_id}")
            
            return {
                "success": True,
                "materials_processed": len(points),
                "supplier_id": supplier_id,
                "collection_name": collection_name,
                "upload_date": current_date
            }
            
        except Exception as e:
            logger.error(f"Error processing price list: {e}")
            raise

    def get_latest_price_list(self, supplier_id: str, limit: int = 1000) -> Dict[str, Any]:
        """Get latest price list for supplier"""
        try:
            collection_name = self._get_collection_name(supplier_id)
            
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            if not any(c.name == collection_name for c in collections.collections):
                return {
                    "supplier_id": supplier_id,
                    "materials": [],
                    "total_count": 0,
                    "message": "No price lists found for this supplier"
                }
            
            # Get all points from collection
            results = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=limit,
                with_payload=True
            )
            
            if isinstance(results, tuple):
                points = results[0]
            else:
                points = results
            
            # Format materials
            materials = []
            for point in points:
                materials.append({
                    "id": str(point.id),
                    "name": point.payload.get("name"),
                    "category": point.payload.get("category"),
                    "unit": point.payload.get("unit"),
                    "price": point.payload.get("price"),
                    "description": point.payload.get("description", ""),
                    "upload_date": point.payload.get("upload_date")
                })
            
            # Sort by upload date (latest first)
            materials.sort(key=lambda x: x.get("upload_date", ""), reverse=True)
            
            return {
                "supplier_id": supplier_id,
                "materials": materials,
                "total_count": len(materials)
            }
            
        except Exception as e:
            logger.error(f"Error getting latest price list: {e}")
            raise

    def get_all_price_lists(self, supplier_id: str) -> Dict[str, Any]:
        """Get all price lists for supplier (grouped by upload date)"""
        try:
            collection_name = self._get_collection_name(supplier_id)
            
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            if not any(c.name == collection_name for c in collections.collections):
                return {
                    "supplier_id": supplier_id,
                    "total_price_lists": 0,
                    "price_lists": []
                }
            
            # Get all points
            all_points = []
            offset = None
            
            while True:
                results = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                
                if isinstance(results, tuple):
                    points, next_offset = results
                else:
                    points = results
                    next_offset = None
                
                all_points.extend(points)
                
                if next_offset is None or not points:
                    break
                    
                offset = next_offset
            
            # Group by upload date
            price_lists_by_date = {}
            for point in all_points:
                upload_date = point.payload.get("upload_date", "unknown")
                if upload_date not in price_lists_by_date:
                    price_lists_by_date[upload_date] = []
                
                price_lists_by_date[upload_date].append({
                    "id": str(point.id),
                    "name": point.payload.get("name"),
                    "category": point.payload.get("category"),
                    "unit": point.payload.get("unit"),
                    "price": point.payload.get("price"),
                    "description": point.payload.get("description", "")
                })
            
            # Format response
            price_lists = []
            for upload_date, materials in price_lists_by_date.items():
                price_lists.append({
                    "upload_date": upload_date,
                    "materials_count": len(materials),
                    "materials": materials
                })
            
            # Sort by date (latest first)
            price_lists.sort(key=lambda x: x["upload_date"], reverse=True)
            
            return {
                "supplier_id": supplier_id,
                "total_price_lists": len(price_lists),
                "price_lists": price_lists
            }
            
        except Exception as e:
            logger.error(f"Error getting all price lists: {e}")
            raise

    def _enforce_price_list_limit(self, collection_name: str, limit: int = 3):
        """Enforce price list limit by keeping only the latest N upload dates"""
        try:
            # Get all points to find unique upload dates
            all_dates = set()
            all_points = []
            offset = None
            
            while True:
                results = self.qdrant_client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    offset=offset,
                    with_payload=True
                )
                
                if isinstance(results, tuple):
                    points, next_offset = results
                else:
                    points = results
                    next_offset = None
                
                for point in points:
                    upload_date = point.payload.get("upload_date")
                    if upload_date:
                        all_dates.add(upload_date)
                    all_points.append(point)
                
                if next_offset is None or not points:
                    break
                    
                offset = next_offset
            
            # If we have more than the limit, remove oldest dates
            if len(all_dates) > limit:
                sorted_dates = sorted(all_dates, reverse=True)  # Latest first
                dates_to_keep = sorted_dates[:limit]
                dates_to_remove = set(all_dates) - set(dates_to_keep)
                
                if dates_to_remove:
                    # Find point IDs to delete
                    points_to_delete = []
                    for point in all_points:
                        upload_date = point.payload.get("upload_date")
                        if upload_date in dates_to_remove:
                            points_to_delete.append(point.id)
                    
                    # Delete old points
                    if points_to_delete:
                        self.qdrant_client.delete(
                            collection_name=collection_name,
                            points_selector=points_to_delete
                        )
                        logger.info(f"Deleted {len(points_to_delete)} old points to enforce limit {limit}")
                        
        except Exception as e:
            logger.error(f"Error enforcing price list limit: {e}")
    
    def delete_supplier_prices(self, supplier_id: str) -> bool:
        """Delete all prices for a supplier"""
        try:
            collection_name = self._get_collection_name(supplier_id)
            
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            if any(c.name == collection_name for c in collections.collections):
                self.qdrant_client.delete_collection(collection_name)
                logger.info(f"Deleted collection for supplier {supplier_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting supplier prices: {e}")
            return False
    
    @staticmethod
    async def validate_categories(categories: List[str]) -> List[str]:
        """Validate categories against existing ones in database"""
        existing_categories = await Category.find_all().to_list()
        existing_names = {cat.name for cat in existing_categories}
        return [cat for cat in categories if cat not in existing_names]
    
    @staticmethod
    async def validate_units(units: List[str]) -> List[str]:
        """Validate units against existing ones in database"""
        existing_units = await Unit.find_all().to_list()
        existing_names = {unit.name for unit in existing_units}
        return [unit for unit in units if unit not in existing_names]
    
    async def _get_collection_dates(self, collection_name: str) -> List[datetime]:
        try:
            response = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=1000,  # Assuming we won't have more than 1000 price entries
                with_payload=True,
                with_vectors=False
            )
            dates = []
            for point in response[0]:
                if 'date' in point.payload:
                    dates.append(datetime.fromisoformat(point.payload['date']))
            return sorted(dates, reverse=True)
        except Exception as e:
            logger.error(f"Error getting collection dates: {str(e)}")
            return []
    
    async def _ensure_supplier_collection(self, supplier_id: str) -> None:
        try:
            collection_name = self._get_collection_name(supplier_id)
            collections = self.qdrant_client.get_collections()
            
            if not any(c.name == collection_name for c in collections.collections):
                # Create new collection for supplier
                self.qdrant_client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload index for date field
                self.qdrant_client.create_payload_index(
                    collection_name=collection_name,
                    field_name="date",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
        except Exception as e:
            logger.error(f"Error creating collection: {str(e)}")
            raise
    
    async def get_all_price_lists_debug(self, supplier_id: str) -> Dict[str, Any]:
        """Get all price lists for a supplier (for debugging)"""
        collection_name = self._get_collection_name(supplier_id)
        
        try:
            # Check if collection exists
            collections = self.qdrant_client.get_collections()
            collection_exists = any(c.name == collection_name for c in collections.collections)
            
            if not collection_exists:
                return {
                    "success": True, 
                    "supplier_id": supplier_id, 
                    "total_price_lists": 0,
                    "price_lists": []
                }
            
            # Get all points
            points, _ = self.qdrant_client.scroll(
                collection_name=collection_name,
                limit=10000,
                with_vectors=False
            )
            
            if not points:
                return {
                    "success": True, 
                    "supplier_id": supplier_id, 
                    "total_price_lists": 0,
                    "price_lists": []
                }
            
            # Group by date
            price_lists_by_date = {}
            for point in points:
                date = point.payload["date"]
                if date not in price_lists_by_date:
                    price_lists_by_date[date] = []
                
                price_lists_by_date[date].append({
                    "id": point.payload["id"],
                    "name": point.payload["name"],
                    "category": point.payload["category"],
                    "unit": point.payload["unit"],
                    "price": point.payload["price"],
                    "description": point.payload.get("description", "")
                })
            
            # Sort by date (newest first)
            sorted_dates = sorted(price_lists_by_date.keys(), reverse=True)
            
            price_lists = []
            for date in sorted_dates:
                price_lists.append({
                    "date": date,
                    "materials_count": len(price_lists_by_date[date]),
                    "materials": sorted(price_lists_by_date[date], key=lambda x: x["name"])
                })
            
            return {
                "success": True,
                "supplier_id": supplier_id,
                "total_price_lists": len(price_lists),
                "price_lists": price_lists
            }
            
        except Exception as e:
            logger.error(f"Error getting all price lists: {str(e)}")
            raise 