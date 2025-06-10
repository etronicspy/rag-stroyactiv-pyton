#!/usr/bin/env python3
"""Test script to initialize MaterialsService and check collection creation"""

import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.materials import MaterialsService

def test_collection():
    print("🔧 Initializing MaterialsService...")
    try:
        service = MaterialsService()
        print("✅ MaterialsService initialized successfully")
        print(f"📋 Collection name: {service.collection_name}")
        
        # Check if collection exists
        collections = service.qdrant_client.get_collections()
        collection_names = [c.name for c in collections.collections]
        print(f"📂 Available collections: {collection_names}")
        
        if service.collection_name in collection_names:
            print("✅ Materials collection exists!")
        else:
            print("❌ Materials collection not found!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_collection() 