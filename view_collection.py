"""
Утилита для просмотра содержимого конкретной коллекции в Qdrant и получения списка коллекций
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
import json
import argparse
from typing import List, Dict, Any

# Load environment variables
load_dotenv('.env.local')

def get_collections() -> List[Dict[str, Any]]:
    """Получает список всех коллекций"""
    try:
        # Initialize Qdrant client
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Get collections list
        collections = client.get_collections()
        
        # Format collections info
        result = []
        for collection in collections.collections:
            info = {
                "name": collection.name,
            }
            # Добавляем дополнительные атрибуты, если они доступны
            for attr in ['points_count', 'status']:
                if hasattr(collection, attr):
                    info[attr] = getattr(collection, attr)
            result.append(info)
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return [{"error": str(e)}]

def format_vector(vector: List[float], max_items: int = 5) -> str:
    """Форматирует вектор для вывода"""
    if not vector:
        return "[]"
    
    if len(vector) <= max_items * 2:
        return json.dumps(vector)
    
    # Показываем первые и последние элементы
    first = vector[:max_items]
    last = vector[-max_items:]
    return f"[{', '.join(map(str, first))}, ..., {', '.join(map(str, last))}] (size: {len(vector)})"

def get_collection_points(collection_name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Получает точки из указанной коллекции"""
    try:
        # Initialize Qdrant client
        client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        
        # Get points using scroll
        response = client.scroll(
            collection_name=collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=True
        )
        
        # Handle response
        if isinstance(response, tuple) and len(response) > 0:
            points = response[0]  # First element contains points
        else:
            points = response
        
        # Convert points to dict
        result = []
        for point in points:
            if hasattr(point, 'id'):
                # If point is a Record object
                point_data = {
                    "id": point.id,
                    "payload": point.payload
                }
                if hasattr(point, 'vector'):
                    point_data["vector"] = list(point.vector) if point.vector is not None else None
            else:
                # If point is already a dict
                point_data = point
                if 'vector' in point_data:
                    point_data['vector'] = list(point_data['vector'])
            
            result.append(point_data)
        
        return result
        
    except Exception as e:
        print(f"Error: {str(e)}")
        print(f"Response type: {type(response)}")
        print(f"Response: {response}")
        return [{"error": str(e)}]

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='View Qdrant collection contents and list collections')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List collections command
    list_parser = subparsers.add_parser('list', help='List all collections')
    
    # View collection command
    view_parser = subparsers.add_parser('view', help='View collection contents')
    view_parser.add_argument('collection', type=str, help='Collection name to view')
    view_parser.add_argument('--limit', type=int, default=100, help='Maximum number of points to retrieve')
    view_parser.add_argument('--show-vectors', action='store_true', help='Show full vectors')
    view_parser.add_argument('--vector-preview', type=int, default=5, help='Number of vector elements to show at start and end')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        collections = get_collections()
        print("\nAvailable collections:")
        print(json.dumps(collections, indent=2, ensure_ascii=False))
    elif args.command == 'view':
    points = get_collection_points(args.collection, args.limit)
    print(f"\nContents of collection '{args.collection}':")
    
    # Format output
    formatted_points = []
    for point in points:
        formatted_point = point.copy()
        if "vector" in formatted_point and not args.show_vectors:
            formatted_point["vector"] = format_vector(formatted_point["vector"], args.vector_preview)
        formatted_points.append(formatted_point)
    
    print(json.dumps(formatted_points, indent=2, ensure_ascii=False)) 
    else:
        parser.print_help() 