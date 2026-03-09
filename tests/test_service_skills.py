from fastapi.testclient import TestClient

from agent_service.main import app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_run_code_python() -> None:
    response = client.post(
        "/skills/run_code",
        json={"language": "python", "code": "print('ok')", "timeout_seconds": 5},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["skill"] == "run_code"
    assert payload["result"]["ok"] is True
    assert "ok" in payload["result"]["stdout"]


def test_search_web_response_shape() -> None:
    response = client.post("/skills/search_web", json={"query": "ironclaw", "max_results": 3})
    assert response.status_code == 200
    payload = response.json()
    assert payload["skill"] == "search_web"
    assert "results" in payload["result"]

