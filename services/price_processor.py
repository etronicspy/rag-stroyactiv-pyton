from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, date
from decimal import Decimal
from core.models.materials import Material, Category, Unit
from core.schemas.materials import RawProduct, RawProductCreate
from qdrant_client import QdrantClient
from qdrant_client.http import models
import os
import uuid
from core.monitoring.logger import get_logger
import numpy as np
from core.config import settings, get_vector_db_client, get_ai_client
from qdrant_client.models import Distance, VectorParams, PointStruct

logger = get_logger(__name__)

class PriceProcessor:
    def __init__(self):
        # Use centralized client factories
        self.qdrant_client = get_vector_db_client()
        self.ai_client = get_ai_client()
        
        # Get configuration
        self.db_config = settings.get_vector_db_config()
        
        # Required columns for basic price processing (backward compatibility)
        self.required_columns = ["name", "use_category", "unit", "price"]
        self.optional_columns = ["description"]
        
        # Extended columns for raw products (new structure)
        self.raw_product_required_columns = ["name", "unit_price", "calc_unit"]
        self.raw_product_optional_columns = {
            "sku": None,
            "use_category": "Общая категория",
            "unit_price_currency": "RUB",
            "unit_calc_price": None,
            "unit_calc_price_currency": "RUB",
            "buy_price": None,
            "buy_price_currency": "RUB",
            "sale_price": None,
            "sale_price_currency": "RUB",
            "count": 1,
            "date_price_change": None
        }
        
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
        """Validate that DataFrame has required columns (backward compatibility)"""
        required_columns = ['name', 'use_category', 'unit', 'price']
        missing_columns = [col for col in required_columns if col not in df.columns]
        return missing_columns
    
    def validate_raw_product_columns(self, df: pd.DataFrame) -> List[str]:
        """Validate that DataFrame has required columns for raw products"""
        missing_columns = [col for col in self.raw_product_required_columns if col not in df.columns]
        return missing_columns
    
    def is_raw_product_format(self, df: pd.DataFrame) -> bool:
        """Detect if DataFrame is in new raw product format"""
        # Check if it has the key raw product columns
        raw_product_indicators = ['unit_price', 'calc_unit', 'sku']
        has_raw_indicators = any(col in df.columns for col in raw_product_indicators)
        
        # Check if it has old format columns
        old_format_indicators = ['price', 'category']
        has_old_indicators = any(col in df.columns for col in old_format_indicators)
        
        return has_raw_indicators and not has_old_indicators

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
            text_columns = ['name', 'use_category', 'unit', 'description']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
            
            return df
        except Exception as e:
            logger.error(f"Error cleaning price data: {e}")
            raise

    def clean_raw_product_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate raw product data"""
        try:
            # Remove rows with empty names
            df = df.dropna(subset=['name'])
            
            # Clean unit_price column (main price field)
            if 'unit_price' in df.columns:
                df['unit_price'] = pd.to_numeric(df['unit_price'], errors='coerce')
                df = df.dropna(subset=['unit_price'])
                df = df[df['unit_price'] >= 0]
            
            # Clean other numeric price columns
            price_columns = ['unit_calc_price', 'buy_price', 'sale_price']
            for col in price_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    df.loc[df[col] < 0, col] = None
            
            # Clean count column
            if 'count' in df.columns:
                df['count'] = pd.to_numeric(df['count'], errors='coerce')
                df['count'] = df['count'].fillna(1)
                df.loc[df['count'] < 0, 'count'] = 1
            
            # Fill missing optional columns with defaults
            for col, default_value in self.raw_product_optional_columns.items():
                if col not in df.columns:
                    df[col] = default_value
                else:
                    if col.endswith('_currency'):
                        df[col] = df[col].fillna('RUB')
                    elif col == 'use_category':
                        df[col] = df[col].fillna('Общая категория')
                    elif col == 'count':
                        df[col] = df[col].fillna(1)
            
            # Clean text columns
            text_columns = ['name', 'sku', 'use_category', 'calc_unit']
            for col in text_columns:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.strip()
                    # Replace 'nan' strings with None for optional fields
                    if col != 'name':  # name is required
                        df.loc[df[col] == 'nan', col] = None
            
            # Handle date_price_change
            if 'date_price_change' in df.columns:
                df['date_price_change'] = pd.to_datetime(df['date_price_change'], errors='coerce')
            
            return df
        except Exception as e:
            logger.error(f"Error cleaning raw product data: {e}")
            raise

    async def process_price_list(self, file_path: str, supplier_id: str, pricelistid: Optional[int] = None) -> Dict[str, Any]:
        """Process price list file and store in vector database (supports both old and new formats)"""
        try:
            # Read and validate file
            df = self.read_price_file(file_path)
            
            # Detect format and validate accordingly
            is_raw_product = self.is_raw_product_format(df)
            
            if is_raw_product:
                # New raw product format
                missing_columns = self.validate_raw_product_columns(df)
                if missing_columns:
                    raise ValueError(f"Missing required columns for raw products: {', '.join(missing_columns)}")
                
                # Generate pricelistid if not provided
                if pricelistid is None:
                    pricelistid = int(datetime.utcnow().timestamp())
                
                df = self.clean_raw_product_data(df)
                return await self._process_raw_products(df, supplier_id, pricelistid)
            else:
                # Legacy format (backward compatibility)
                missing_columns = self.validate_required_columns(df)
                if missing_columns:
                    raise ValueError(f"Missing required columns: {', '.join(missing_columns)}")
                
                df = self.clean_price_data(df)
                return await self._process_legacy_format(df, supplier_id)
            
        except Exception as e:
            logger.error(f"Error processing price list: {e}")
            raise

    async def _process_raw_products(self, df: pd.DataFrame, supplier_id: str, pricelistid: int) -> Dict[str, Any]:
        """Process raw products in new extended format"""
        if df.empty:
            raise ValueError("No valid data found after cleaning")
        
        # Prepare collection (using supplier_id as string for collection name)
        collection_name = self._get_collection_name(str(supplier_id))
        self._ensure_collection_exists(collection_name)
        
        # Process raw products and create embeddings
        points = []
        current_time = datetime.utcnow()
        
        for _, row in df.iterrows():
            try:
                # Create text for embedding (new fields included)
                text_parts = [
                    str(row['name']),
                    str(row.get('sku', '')) if pd.notna(row.get('sku')) else '',
                    str(row.get('use_category', '')) if pd.notna(row.get('use_category')) else '',
                    str(row.get('calc_unit', '')) if pd.notna(row.get('calc_unit')) else ''
                ]
                text_for_embedding = ' '.join(filter(None, text_parts))
                embedding = await self._get_embedding(text_for_embedding)
                
                # Create extended payload
                payload = {
                    "name": str(row['name']),
                    "sku": str(row['sku']) if pd.notna(row.get('sku')) else None,
                    "use_category": str(row.get('use_category', 'Общая категория')),
                    
                    # Pricing information
                    "unit_price": float(row['unit_price']) if pd.notna(row['unit_price']) else None,
                    "unit_price_currency": str(row.get('unit_price_currency', 'RUB')),
                    "unit_calc_price": float(row['unit_calc_price']) if pd.notna(row.get('unit_calc_price')) else None,
                    "unit_calc_price_currency": str(row.get('unit_calc_price_currency', 'RUB')),
                    "buy_price": float(row['buy_price']) if pd.notna(row.get('buy_price')) else None,
                    "buy_price_currency": str(row.get('buy_price_currency', 'RUB')),
                    "sale_price": float(row['sale_price']) if pd.notna(row.get('sale_price')) else None,
                    "sale_price_currency": str(row.get('sale_price_currency', 'RUB')),
                    
                    # Units and quantities
                    "calc_unit": str(row.get('calc_unit')) if pd.notna(row.get('calc_unit')) else None,
                    "count": int(row.get('count', 1)) if pd.notna(row.get('count')) else 1,
                    
                    # Metadata
                    "pricelistid": pricelistid,
                    "supplier_id": supplier_id,
                    "is_processed": False,
                    "date_price_change": row['date_price_change'].isoformat() if pd.notna(row.get('date_price_change')) else None,
                    "created": current_time.isoformat(),
                    "modified": current_time.isoformat(),
                    "upload_date": current_time.isoformat()
                }
                
                # Create point
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
                points.append(point)
                
            except Exception as e:
                logger.warning(f"Error processing raw product {row.get('name', 'unknown')}: {e}")
                continue
        
        if not points:
            raise ValueError("No valid points created from data")
        
        # Store in Qdrant
        self.qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        # Enforce limit of 5 price lists per supplier
        self._enforce_price_list_limit(collection_name, limit=5)
        
        logger.info(f"Successfully processed {len(points)} raw products for supplier {supplier_id}")
        
        return {
            "success": True,
            "raw_products_processed": len(points),
            "supplier_id": supplier_id,
            "pricelistid": pricelistid,
            "collection_name": collection_name,
            "upload_date": current_time.isoformat()
        }

    async def _process_legacy_format(self, df: pd.DataFrame, supplier_id: str) -> Dict[str, Any]:
        """Process legacy price list format (backward compatibility)"""
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
                # Create text for embedding (legacy format)
                text_for_embedding = f"{row['name']} {row['use_category']} {row.get('description', '')}"
                embedding = await self._get_embedding(text_for_embedding)
                
                # Create point (legacy payload structure)
                point_id = str(uuid.uuid4())
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "name": row['name'],
                        "use_category": row['use_category'],  # Updated field name
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
        
        # Enforce limit of 3 price lists per supplier (legacy)
        self._enforce_price_list_limit(collection_name, limit=3)
        
        logger.info(f"Successfully processed {len(points)} materials for supplier {supplier_id}")
        
        return {
            "success": True,
            "materials_processed": len(points),
            "supplier_id": supplier_id,
            "collection_name": collection_name,
            "upload_date": current_date
        }

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
            
            # Format materials (support both legacy and new formats)
            materials = []
            for point in points:
                material = {
                    "id": str(point.id),
                    "name": point.payload.get("name"),
                    "use_category": point.payload.get("use_category"),
                    "upload_date": point.payload.get("upload_date")
                }
                
                # Legacy format fields
                if point.payload.get("unit") is not None:
                    material["unit"] = point.payload.get("unit")
                if point.payload.get("price") is not None:
                    material["price"] = point.payload.get("price")
                if point.payload.get("description") is not None:
                    material["description"] = point.payload.get("description", "")
                
                # Extended format fields
                if point.payload.get("sku") is not None:
                    material["sku"] = point.payload.get("sku")
                if point.payload.get("unit_price") is not None:
                    material["unit_price"] = point.payload.get("unit_price")
                    material["unit_price_currency"] = point.payload.get("unit_price_currency")
                if point.payload.get("unit_calc_price") is not None:
                    material["unit_calc_price"] = point.payload.get("unit_calc_price")
                    material["unit_calc_price_currency"] = point.payload.get("unit_calc_price_currency")
                if point.payload.get("buy_price") is not None:
                    material["buy_price"] = point.payload.get("buy_price")
                    material["buy_price_currency"] = point.payload.get("buy_price_currency")
                if point.payload.get("sale_price") is not None:
                    material["sale_price"] = point.payload.get("sale_price")
                    material["sale_price_currency"] = point.payload.get("sale_price_currency")
                if point.payload.get("calc_unit") is not None:
                    material["calc_unit"] = point.payload.get("calc_unit")
                if point.payload.get("count") is not None:
                    material["count"] = point.payload.get("count")
                if point.payload.get("pricelistid") is not None:
                    material["pricelistid"] = point.payload.get("pricelistid")
                if point.payload.get("is_processed") is not None:
                    material["is_processed"] = point.payload.get("is_processed")
                if point.payload.get("date_price_change") is not None:
                    material["date_price_change"] = point.payload.get("date_price_change")
                
                materials.append(material)
            
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
                
                # Create material entry supporting both legacy and extended formats
                material = {
                    "id": str(point.id),
                    "name": point.payload.get("name"),
                    "use_category": point.payload.get("use_category"),
                    "upload_date": point.payload.get("upload_date")
                }
                
                # Legacy format fields
                if point.payload.get("unit") is not None:
                    material["unit"] = point.payload.get("unit")
                if point.payload.get("price") is not None:
                    material["price"] = point.payload.get("price")
                if point.payload.get("description") is not None:
                    material["description"] = point.payload.get("description", "")
                
                # Extended format fields
                if point.payload.get("sku") is not None:
                    material["sku"] = point.payload.get("sku")
                if point.payload.get("unit_price") is not None:
                    material["unit_price"] = point.payload.get("unit_price")
                    material["unit_price_currency"] = point.payload.get("unit_price_currency")
                if point.payload.get("unit_calc_price") is not None:
                    material["unit_calc_price"] = point.payload.get("unit_calc_price")
                    material["unit_calc_price_currency"] = point.payload.get("unit_calc_price_currency")
                if point.payload.get("buy_price") is not None:
                    material["buy_price"] = point.payload.get("buy_price")
                    material["buy_price_currency"] = point.payload.get("buy_price_currency")
                if point.payload.get("sale_price") is not None:
                    material["sale_price"] = point.payload.get("sale_price")
                    material["sale_price_currency"] = point.payload.get("sale_price_currency")
                if point.payload.get("calc_unit") is not None:
                    material["calc_unit"] = point.payload.get("calc_unit")
                if point.payload.get("count") is not None:
                    material["count"] = point.payload.get("count")
                if point.payload.get("pricelistid") is not None:
                    material["pricelistid"] = point.payload.get("pricelistid")
                if point.payload.get("is_processed") is not None:
                    material["is_processed"] = point.payload.get("is_processed")
                if point.payload.get("date_price_change") is not None:
                    material["date_price_change"] = point.payload.get("date_price_change")
                
                price_lists_by_date[upload_date].append(material)
            
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