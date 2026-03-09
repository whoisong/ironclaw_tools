from __future__ import annotations

from agent_service.vision.fara_client import FaraClient


def test_fara_client_calls_generate_only(monkeypatch) -> None:
    calls: list[str] = []

    class _DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, str]:
            return {"response": '{"action":"none","reason":"ok"}'}

    class _DummyClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, url: str, json: dict | None = None):
            calls.append(url)
            return _DummyResponse()

    monkeypatch.setattr("agent_service.vision.fara_client.httpx.Client", _DummyClient)

    client = FaraClient(base_url="http://localhost:11434", model_name="fara")
    result = client.predict_action("test goal", screenshot_b64="abc")
    assert result["action"] == "none"
    assert len(calls) == 1
    assert calls[0].endswith("/api/generate")
    assert "/v1/chat/completions" not in calls[0]
