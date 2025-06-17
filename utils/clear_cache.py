#!/usr/bin/env python3
"""Clear database factory cache"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.database.factories import DatabaseFactory

if __name__ == "__main__":
    print("🧹 Clearing database factory cache...")
    DatabaseFactory.clear_cache()
    print("✅ Cache cleared successfully!")
    
    # Show cache info
    cache_info = DatabaseFactory.get_cache_info()
    print("📊 Cache statistics:")
    for db_type, info in cache_info.items():
        print(f"   └─ {db_type}: {info}") 