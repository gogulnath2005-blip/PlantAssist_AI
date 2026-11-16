from fastapi.testclient import TestClient
from app.main import app

def test_health_endpoint():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_empty_question_is_rejected():
    response = TestClient(app).post("/api/ask", json={"question": ""})
    assert response.status_code == 422

def test_ask_requires_index():
    import app.main as main_module
    old_index, old_retriever = main_module._index, main_module._retriever
    try:
        main_module._index = None
        main_module._retriever = None
        response = TestClient(app).post("/api/ask", json={"question":"What is the sampling plan?"})
        assert response.status_code == 503
    finally:
        main_module._index, main_module._retriever = old_index, old_retriever
