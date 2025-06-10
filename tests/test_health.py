def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/health/config")
    assert response.status_code == 200
    data = response.json()
    assert "services" in data
    # Проверяем, что есть информация о сервисах
    services = data["services"]
    # Должен быть либо openai, либо huggingface, либо ai_provider
    ai_service_exists = any(key in services for key in ["openai", "huggingface", "ai_provider"])
    assert ai_service_exists, f"AI service not found in services: {list(services.keys())}"
    # Должен быть либо qdrant, либо vector_db
    db_service_exists = any(key in services for key in ["qdrant", "vector_db"])
    assert db_service_exists, f"DB service not found in services: {list(services.keys())}"

def test_basic_health_check(client):
    """Test basic health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "environment" in data 