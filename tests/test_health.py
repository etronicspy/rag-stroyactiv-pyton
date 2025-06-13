def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/health/config")
    assert response.status_code == 200
    data = response.json()
    assert "configuration" in data
    # Проверяем, что есть информация о конфигурации
    configuration = data["configuration"]
    # Должен быть либо openai, либо huggingface, либо ai_provider
    ai_service_exists = any(key in configuration for key in ["openai", "huggingface", "ai_provider"])
    assert ai_service_exists, f"AI service not found in configuration: {list(configuration.keys())}"
    # Должен быть либо database_type, либо qdrant, либо vector_db  
    db_service_exists = any(key in configuration for key in ["database_type", "qdrant", "vector_db"])
    assert db_service_exists, f"DB service not found in configuration: {list(configuration.keys())}"

def test_basic_health_check(client):
    """Test basic health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data 