import pytest

from app.core.agent_engine import OpenClawRuntime


class _MockResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _MockAsyncClient:
    def __init__(self, response):
        self.response = response
        self.last_url = None
        self.last_json = None
        self.last_headers = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json, headers):
        self.last_url = url
        self.last_json = json
        self.last_headers = headers
        return self.response


@pytest.mark.asyncio
async def test_openclaw_runtime_run_success_with_openai_shape(monkeypatch):
    monkeypatch.setenv("OPENCLAW_API_URL", "http://openclaw.local")
    monkeypatch.setenv("OPENCLAW_API_KEY", "test-key")
    monkeypatch.setenv("OPENCLAW_MODEL", "openai-codex/gpt-5.3-codex")

    response = _MockResponse(
        {
            "choices": [
                {
                    "message": {
                        "content": "Hello from OpenClaw"
                    }
                }
            ]
        }
    )
    client = _MockAsyncClient(response)

    import app.core.agent_engine as agent_engine_module

    monkeypatch.setattr(
        agent_engine_module.httpx,
        "AsyncClient",
        lambda timeout: client,
    )

    runtime = OpenClawRuntime()
    text = await runtime.run(
        system_prompt="You are helpful",
        message="Hi",
        memory=[{"role": "assistant", "content": "Previous"}],
    )

    assert text == "Hello from OpenClaw"
    assert client.last_url == "http://openclaw.local/v1/chat/completions"
    assert client.last_headers["Authorization"] == "Bearer test-key"
    assert client.last_json["model"] == "openai-codex/gpt-5.3-codex"
    assert client.last_json["messages"][0]["role"] == "system"
    assert client.last_json["messages"][-1]["role"] == "user"


@pytest.mark.asyncio
async def test_openclaw_runtime_run_supports_simple_response_shape(monkeypatch):
    monkeypatch.setenv("OPENCLAW_API_URL", "http://localhost:8080")
    monkeypatch.delenv("OPENCLAW_API_KEY", raising=False)

    response = _MockResponse({"response": "Simple shape"})
    client = _MockAsyncClient(response)

    import app.core.agent_engine as agent_engine_module

    monkeypatch.setattr(
        agent_engine_module.httpx,
        "AsyncClient",
        lambda timeout: client,
    )

    runtime = OpenClawRuntime()
    text = await runtime.run(
        system_prompt="System",
        message="Hi",
        memory=[],
    )

    assert text == "Simple shape"
    assert "Authorization" not in client.last_headers


@pytest.mark.asyncio
async def test_openclaw_runtime_raises_when_no_text(monkeypatch):
    response = _MockResponse({"choices": []})
    client = _MockAsyncClient(response)

    import app.core.agent_engine as agent_engine_module

    monkeypatch.setattr(
        agent_engine_module.httpx,
        "AsyncClient",
        lambda timeout: client,
    )

    runtime = OpenClawRuntime()

    with pytest.raises(RuntimeError) as exc:
        await runtime.run(system_prompt="System", message="Hi", memory=[])

    assert "missing assistant text" in str(exc.value)
