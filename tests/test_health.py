def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/api/v1/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "openai" in data["services"]
    assert "qdrant" in data["services"] 