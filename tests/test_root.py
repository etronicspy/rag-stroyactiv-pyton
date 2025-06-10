def test_root(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs_url" in data
    assert data["message"] == "Welcome to Construction Materials API"
    assert data["docs_url"] == "/docs" 