# 🔧 API Examples - Практические примеры использования

Коллекция готовых к использованию примеров для всех эндпоинтов RAG Construction Materials API.

## 🐍 Python Examples

### Продвинутый поиск

```python
import requests
import json

class MaterialsAPIClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        
    def advanced_search(self, query, search_type="hybrid", **kwargs):
        """Продвинутый поиск материалов"""
        data = {
            "query": query,
            "search_type": search_type,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/api/v1/search/advanced",
            json=data
        )
        return response.json()
    
    def get_suggestions(self, query, limit=10):
        """Получение предложений автодополнения"""
        params = {"query": query, "limit": limit}
        response = requests.get(
            f"{self.base_url}/api/v1/search/suggestions",
            params=params
        )
        return response.json()

# Использование клиента
client = MaterialsAPIClient()

# Гибридный поиск с фильтрацией
results = client.advanced_search(
    query="портландцемент М500",
    search_type="hybrid",
    filters={
        "categories": ["Cement"],
        "units": ["bag", "kg"],
        "similarity_threshold": 0.8
    },
    sort_options=[
        {"field": "relevance", "direction": "desc"},
        {"field": "name", "direction": "asc"}
    ],
    pagination={"page": 1, "page_size": 20}
)

print(f"Найдено материалов: {results['pagination']['total_results']}")
for material in results['results']:
    print(f"- {material['name']} ({material['score']:.2f})")
```

### Обработка прайс-листов

```python
import requests
from pathlib import Path

def upload_pricelist(file_path, supplier_name=None):
    """Загрузка и обработка прайс-листа"""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {}
        if supplier_name:
            data['supplier_name'] = supplier_name
            
        response = requests.post(
            "http://localhost:8000/api/v1/prices/process",
            files=files,
            data=data
        )
    return response.json()

# Загрузка Excel файла
result = upload_pricelist(
    "pricelist.xlsx", 
    supplier_name="ООО СтройМатериалы"
)

print(f"Статус: {result['status']}")
print(f"Обработано строк: {result['summary']['processed_rows']}")
print(f"Создано материалов: {result['summary']['created_materials']}")
```

### Управление материалами

```python
def create_material(name, category, unit, description=None, sku=None):
    """Создание нового материала"""
    data = {
        "name": name,
        "use_category": category,
        "unit": unit
    }
    if description:
        data["description"] = description
    if sku:
        data["sku"] = sku
        
    response = requests.post(
        "http://localhost:8000/api/v1/reference/materials",
        json=data
    )
    return response.json()

def get_materials(category=None, limit=50):
    """Получение списка материалов"""
    params = {"limit": limit}
    if category:
        params["category"] = category
        
    response = requests.get(
        "http://localhost:8000/api/v1/reference/materials",
        params=params
    )
    return response.json()

# Создание материала
new_material = create_material(
    name="Портландцемент М400",
    category="Cement",
    unit="bag",
    description="Цемент марки М400 для общих строительных работ",
    sku="CEM-M400-25KG"
)

# Получение всех цементов
cement_materials = get_materials(category="Cement")
```

## 🌐 JavaScript/Node.js Examples

### Продвинутый поиск

```javascript
class MaterialsAPI {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }
    
    async advancedSearch(searchParams) {
        const response = await fetch(`${this.baseURL}/api/v1/search/advanced`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(searchParams)
        });
        
        if (!response.ok) {
            throw new Error(`Search failed: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async getSuggestions(query, limit = 10) {
        const params = new URLSearchParams({ query, limit });
        const response = await fetch(
            `${this.baseURL}/api/v1/search/suggestions?${params}`
        );
        return await response.json();
    }
    
    async getPopularQueries(limit = 20) {
        const response = await fetch(
            `${this.baseURL}/api/v1/search/popular-queries?limit=${limit}`
        );
        return await response.json();
    }
}

// Использование
const api = new MaterialsAPI();

// Поиск с автодополнением
async function searchWithSuggestions(userQuery) {
    try {
        // Получаем предложения
        const suggestions = await api.getSuggestions(userQuery, 5);
        console.log('Предложения:', suggestions.suggestions);
        
        // Выполняем поиск
        const results = await api.advancedSearch({
            query: userQuery,
            search_type: 'hybrid',
            filters: {
                similarity_threshold: 0.7
            },
            highlight: {
                enabled: true,
                fields: ['name', 'description']
            }
        });
        
        console.log(`Найдено: ${results.pagination.total_results} материалов`);
        return results;
        
    } catch (error) {
        console.error('Ошибка поиска:', error);
    }
}
```

### Загрузка файлов

```javascript
async function uploadPricelist(file, supplierName) {
    const formData = new FormData();
    formData.append('file', file);
    if (supplierName) {
        formData.append('supplier_name', supplierName);
    }
    
    try {
        const response = await fetch('/api/v1/prices/process', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Обработка результата
        if (result.status === 'success') {
            console.log(`✅ Загружено ${result.summary.processed_rows} строк`);
            console.log(`📦 Создано ${result.summary.created_materials} материалов`);
            
            if (result.warnings.length > 0) {
                console.warn('⚠️ Предупреждения:', result.warnings);
            }
        }
        
        return result;
        
    } catch (error) {
        console.error('Ошибка загрузки:', error);
        throw error;
    }
}

// Использование в HTML форме
document.getElementById('upload-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const fileInput = document.getElementById('file-input');
    const supplierInput = document.getElementById('supplier-input');
    
    if (fileInput.files.length > 0) {
        await uploadPricelist(fileInput.files[0], supplierInput.value);
    }
});
```

## 🔧 cURL Examples

### Базовые операции

```bash
# Продвинутый поиск с фильтрацией
curl -X POST "http://localhost:8000/api/v1/search/advanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "цемент М500",
    "search_type": "hybrid",
    "filters": {
      "categories": ["Cement"],
      "similarity_threshold": 0.8
    },
    "pagination": {"page": 1, "page_size": 10}
  }'

# Получение предложений автодополнения
curl -X GET "http://localhost:8000/api/v1/search/suggestions?query=цемент&limit=5"

# Получение популярных запросов
curl -X GET "http://localhost:8000/api/v1/search/popular-queries?limit=10&period=week"

# Загрузка прайс-листа
curl -X POST "http://localhost:8000/api/v1/prices/process" \
  -F "file=@pricelist.xlsx" \
  -F "supplier_name=ООО СтройМат"

# Создание материала
curl -X POST "http://localhost:8000/api/v1/reference/materials" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Портландцемент М500",
    "use_category": "Cement",
    "unit": "bag",
    "description": "Высококачественный цемент"
  }'

# Получение списка материалов
curl -X GET "http://localhost:8000/api/v1/reference/materials?category=Cement&limit=20"

# Проверка здоровья системы
curl -X GET "http://localhost:8000/api/v1/health"
```

## 🔍 Сценарии использования

### Сценарий 1: Поиск с подсветкой и фильтрацией

```python
def search_with_highlighting(query, categories=None):
    """Поиск с подсветкой совпадений"""
    search_params = {
        "query": query,
        "search_type": "hybrid",
        "highlight": {
            "enabled": True,
            "fields": ["name", "description", "use_category"]
        }
    }
    
    if categories:
        search_params["filters"] = {"categories": categories}
    
    response = requests.post(
        "http://localhost:8000/api/v1/search/advanced",
        json=search_params
    )
    
    results = response.json()
    
    # Вывод результатов с подсветкой
    for item in results['results']:
        print(f"\n📦 {item['name']} (Score: {item['score']:.2f})")
        
        if 'highlights' in item:
            if 'name' in item['highlights']:
                print(f"   Название: {item['highlights']['name']}")
            if 'description' in item['highlights']:
                print(f"   Описание: {item['highlights']['description']}")
    
    return results

# Использование
results = search_with_highlighting(
    "портландцемент для фундамента",
    categories=["Cement", "Concrete"]
)
```

### Сценарий 2: Batch загрузка и валидация

```python
def batch_upload_with_validation(file_paths):
    """Batch загрузка множества файлов с валидацией"""
    results = []
    
    for file_path in file_paths:
        # Сначала валидируем файл
        with open(file_path, 'rb') as f:
            validation_response = requests.post(
                "http://localhost:8000/api/v1/prices/validate",
                files={'file': f}
            )
        
        validation = validation_response.json()
        
        if validation['validation_result']['is_valid']:
            # Если валидация прошла - загружаем
            with open(file_path, 'rb') as f:
                upload_response = requests.post(
                    "http://localhost:8000/api/v1/prices/process",
                    files={'file': f},
                    data={'batch_size': '100'}
                )
            
            results.append({
                'file': file_path,
                'status': 'success',
                'result': upload_response.json()
            })
        else:
            results.append({
                'file': file_path,
                'status': 'validation_failed',
                'errors': validation['validation_result']['errors']
            })
    
    return results
```

### Сценарий 3: Мониторинг и аналитика

```javascript
class MaterialsAnalytics {
    constructor(apiBase = 'http://localhost:8000') {
        this.apiBase = apiBase;
    }
    
    async getSystemHealth() {
        const response = await fetch(`${this.apiBase}/api/v1/health/detailed`);
        return await response.json();
    }
    
    async getSearchAnalytics(period = 'week') {
        const response = await fetch(
            `${this.apiBase}/api/v1/search/analytics?period=${period}`
        );
        return await response.json();
    }
    
    async generateReport() {
        const [health, analytics, popular] = await Promise.all([
            this.getSystemHealth(),
            this.getSearchAnalytics(),
            fetch(`${this.apiBase}/api/v1/search/popular-queries?limit=10`)
                .then(r => r.json())
        ]);
        
        return {
            timestamp: new Date().toISOString(),
            system_status: health.status,
            total_searches: analytics.analytics.total_searches,
            avg_search_time: analytics.analytics.avg_search_time_ms,
            top_queries: popular.popular_queries.slice(0, 5),
            database_health: {
                postgresql: health.components.postgresql.status,
                qdrant: health.components.qdrant.status,
                materials_count: health.components.postgresql.tables.materials
            }
        };
    }
}

// Использование для мониторинга
const analytics = new MaterialsAnalytics();

setInterval(async () => {
    const report = await analytics.generateReport();
    console.log('📊 System Report:', report);
    
    // Отправка в систему мониторинга
    if (report.system_status !== 'healthy') {
        console.warn('⚠️ System health issues detected!');
    }
}, 60000); // каждую минуту
```

## 🔄 Обработка ошибок

### Python пример с обработкой ошибок

```python
import requests
from requests.exceptions import RequestException, Timeout

class MaterialsAPIError(Exception):
    def __init__(self, message, status_code=None, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)

def safe_api_call(func):
    """Декоратор для безопасных API вызовов"""
    def wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            
            if not response.ok:
                error_data = response.json() if response.content else {}
                raise MaterialsAPIError(
                    error_data.get('error', {}).get('message', 'Unknown error'),
                    response.status_code,
                    error_data.get('error', {}).get('details')
                )
            
            return response.json()
            
        except Timeout:
            raise MaterialsAPIError("Request timeout")
        except RequestException as e:
            raise MaterialsAPIError(f"Network error: {e}")
        except ValueError as e:
            raise MaterialsAPIError(f"Invalid JSON response: {e}")
    
    return wrapper

@safe_api_call
def search_materials(query, **params):
    return requests.post(
        "http://localhost:8000/api/v1/search/advanced",
        json={"query": query, **params},
        timeout=30
    )

# Использование с обработкой ошибок
try:
    results = search_materials("цемент", search_type="hybrid")
    print(f"Найдено: {len(results['results'])} материалов")
    
except MaterialsAPIError as e:
    if e.status_code == 429:
        print("⚠️ Превышен лимит запросов, попробуйте позже")
    elif e.status_code == 422:
        print(f"❌ Ошибка валидации: {e.details}")
    else:
        print(f"❌ Ошибка API: {e.message}")
```

## 🚀 Продвинутые примеры

### Реактивный поиск (React)

```jsx
import { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';

function MaterialSearch() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState([]);
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    
    // Дебаунсированный поиск предложений
    const debouncedGetSuggestions = useCallback(
        debounce(async (searchQuery) => {
            if (searchQuery.length < 2) return;
            
            try {
                const response = await fetch(
                    `/api/v1/search/suggestions?query=${encodeURIComponent(searchQuery)}&limit=5`
                );
                const data = await response.json();
                setSuggestions(data.suggestions);
            } catch (error) {
                console.error('Error fetching suggestions:', error);
            }
        }, 300),
        []
    );
    
    // Основной поиск
    const performSearch = async (searchQuery) => {
        if (!searchQuery.trim()) return;
        
        setLoading(true);
        try {
            const response = await fetch('/api/v1/search/advanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: searchQuery,
                    search_type: 'hybrid',
                    highlight: { enabled: true, fields: ['name', 'description'] },
                    pagination: { page: 1, page_size: 20 }
                })
            });
            
            const data = await response.json();
            setResults(data.results);
        } catch (error) {
            console.error('Search error:', error);
        } finally {
            setLoading(false);
        }
    };
    
    useEffect(() => {
        debouncedGetSuggestions(query);
    }, [query, debouncedGetSuggestions]);
    
    return (
        <div className="material-search">
            <div className="search-input-container">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && performSearch(query)}
                    placeholder="Поиск материалов..."
                />
                
                {suggestions.length > 0 && (
                    <ul className="suggestions">
                        {suggestions.map((suggestion, index) => (
                            <li
                                key={index}
                                onClick={() => {
                                    setQuery(suggestion.text);
                                    performSearch(suggestion.text);
                                    setSuggestions([]);
                                }}
                            >
                                {suggestion.text}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
            
            {loading && <div>Поиск...</div>}
            
            <div className="search-results">
                {results.map((material) => (
                    <div key={material.id} className="material-card">
                        <h3 dangerouslySetInnerHTML={{ 
                            __html: material.highlights?.name || material.name 
                        }} />
                        <p dangerouslySetInnerHTML={{ 
                            __html: material.highlights?.description || material.description 
                        }} />
                        <span className="score">Score: {material.score.toFixed(2)}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}
```

---

**📋 Готовые к использованию примеры**  
**🔄 Обновлено**: 2024-01-15  
**💡 Tip**: Используйте эти примеры как основу для своих приложений 