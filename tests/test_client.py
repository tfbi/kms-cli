import json

import httpx
import pytest

from kms_cli.client import KnowledgeClient
from kms_cli.config import EndpointConfig, KmsConfig
from kms_cli.errors import AuthError, HttpRequestError, HttpStatusError, InvalidJsonError


def make_config() -> KmsConfig:
    return KmsConfig(
        base_url="https://kms.example.test",
        token=None,
        endpoints={
            "me": EndpointConfig("GET", "/me"),
            "kbs": EndpointConfig("POST", "/kbs"),
            "channels": EndpointConfig("GET", "/channels"),
            "faqs": EndpointConfig("POST", "/faqs"),
            "faq_detail": EndpointConfig("GET", "/faq"),
        },
        path=None,  # type: ignore[arg-type]
    )


def test_get_channels_uses_query_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["authorization"] = request.headers["authorization"]
        seen["tenant_id"] = request.headers["tenant-id"]
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"items": []})

    client = KnowledgeClient(make_config(), token="abc", transport=httpx.MockTransport(handler))

    assert client.channels("kb-1") == {"items": []}
    assert seen["method"] == "GET"
    assert seen["authorization"] == "Bearer abc"
    assert seen["tenant_id"] == "2"
    assert seen["url"] == "https://kms.example.test/channels?knowledgeId=kb-1"


def test_post_faqs_uses_json_body_with_pagination():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"items": []})

    client = KnowledgeClient(make_config(), token="abc", transport=httpx.MockTransport(handler))

    client.faqs("ch-1", page=2, page_size=50)

    assert seen["method"] == "POST"
    assert seen["content_type"].startswith("application/json")
    assert seen["body"] == {"channelId": "ch-1", "pageNo": 2, "pageSize": 50}


def test_default_pagination_uses_page_size_ten():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        seen["tenant_id"] = request.headers["tenant-id"]
        return httpx.Response(200, json={"items": []})

    client = KnowledgeClient(make_config(), token="abc", transport=httpx.MockTransport(handler))

    client.kbs()

    assert seen["body"] == {"pageNo": 1, "pageSize": 10}
    assert seen["tenant_id"] == "2"


def test_raises_auth_error_for_401():
    client = KnowledgeClient(
        make_config(),
        token="abc",
        transport=httpx.MockTransport(lambda request: httpx.Response(401, json={"error": "expired"})),
    )

    with pytest.raises(AuthError):
        client.me()


def test_raises_status_error_for_non_success():
    client = KnowledgeClient(
        make_config(),
        token="abc",
        transport=httpx.MockTransport(lambda request: httpx.Response(500, text="boom")),
    )

    with pytest.raises(HttpStatusError, match="HTTP 500"):
        client.me()


def test_raises_invalid_json_for_bad_body():
    client = KnowledgeClient(
        make_config(),
        token="abc",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, text="not-json")),
    )

    with pytest.raises(InvalidJsonError):
        client.me()


def test_raises_request_error_when_transport_fails():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connect failed", request=request)

    client = KnowledgeClient(make_config(), token="abc", transport=httpx.MockTransport(handler))

    with pytest.raises(HttpRequestError, match="请求失败"):
        client.me()


def test_with_token_preserves_transport_and_uses_new_bearer_token():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["authorization"] = request.headers["authorization"]
        return httpx.Response(200, json={"ok": True})

    client = KnowledgeClient(make_config(), token="old", transport=httpx.MockTransport(handler))
    refreshed = client.with_token("new")

    assert refreshed.me() == {"ok": True}
    assert seen["authorization"] == "Bearer new"


def test_close_closes_underlying_client(monkeypatch):
    closed = []
    client = KnowledgeClient(
        make_config(),
        token="abc",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={})),
    )
    monkeypatch.setattr(client._client, "close", lambda: closed.append(True))

    client.close()

    assert closed == [True]


def test_context_manager_closes_without_error():
    with KnowledgeClient(
        make_config(),
        token="abc",
        transport=httpx.MockTransport(lambda request: httpx.Response(200, json={"ok": True})),
    ) as client:
        assert client.me() == {"ok": True}
