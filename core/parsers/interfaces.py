print("DEBUG: core/parsers/interfaces.py loaded")

from typing import Any, Dict, List, Optional, Protocol

class IMaterialParser(Protocol):
    def parse(self, data: Any) -> 'MaterialParseData':
        ...

class MaterialParseData:
    def __init__(self, name: str, description: str, properties: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.properties = properties or {}

class AIParseResult:
    def __init__(self, success: bool, data: Optional[MaterialParseData] = None, error: Optional[str] = None):
        self.success = success
        self.data = data
        self.error = error

# Add other interfaces/types as needed for your project 