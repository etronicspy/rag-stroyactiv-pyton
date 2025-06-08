# RAG Search API

REST API сервис для семантического поиска с использованием RAG (Retrieval-Augmented Generation) на основе OpenAI и Qdrant.

## Функциональность

- Семантический поиск по базе знаний
- Возвращает релевантные результаты с источниками
- Использует embeddings от OpenAI для векторного поиска
- Хранение векторов в Qdrant

## Технологии

- FastAPI
- OpenAI API (embeddings)
- Qdrant Vector Database
- Python 3.8+

## Установка

1. Клонируйте репозиторий:
```bash
git clone [your-repo-url]
cd [your-repo-name]
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/MacOS
# или
.\venv\Scripts\activate  # для Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Настройте переменные окружения:
   - Создайте файл `env.local` на основе примера ниже:
```
OPENAI_API_KEY=your_openai_key_here
QDRANT_URL=your_qdrant_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
```

## Запуск

1. Активируйте виртуальное окружение (если еще не активировано):
```bash
source venv/bin/activate  # для Linux/MacOS
# или
.\venv\Scripts\activate  # для Windows
```

2. Запустите сервер:
```bash
python main.py
```

Сервер будет доступен по адресу: `http://localhost:8000`

## API Endpoints

### POST /search

Поиск релевантной информации по запросу.

**Request:**
```json
{
    "query": "ваш поисковый запрос",
    "limit": 5
}
```

**Response:**
```json
{
    "query": "ваш поисковый запрос",
    "matches": [
        {
            "score": 0.95,
            "payload": {
                "text": "найденный текст",
                "source": "url источника"
            }
        }
    ],
    "sources": ["url1", "url2"]
}
```

## Swagger Documentation

API документация доступна по адресу: `http://localhost:8000/docs`

## Разработка

1. Убедитесь, что все зависимости установлены
2. Создайте новую ветку для ваших изменений
3. Следуйте PEP 8 для Python кода
4. Добавьте тесты для новой функциональности
5. Обновите документацию при необходимости 