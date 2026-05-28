import httpx
import pytest

from kms_cli.client import KnowledgeClient
from kms_cli.config import EndpointConfig, KmsConfig
from kms_cli.errors import AuthError, HttpStatusError, InvalidJsonError


def make_config() -> KmsConfig:
    return KmsConfig(
        base_url="https://kms.example.test",
        token=None,
        endpoints={
            "me": EndpointConfig("GET", "/me"),
            "spaces": EndpointConfig("POST", "/spaces"),
            "channels": EndpointConfig("GET", "/channels"),
            "faqs": EndpointConfig("POST", "/faqs"),
            "faq_detail": EndpointConfig("GET", "/faq"),
        },
        path=None,  # type: ignore[arg-type]
    )


def test_get_channels_uses_query_params():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"items": []})

    client = KnowledgeClient(make_config(), token="abc", transport=httpx.MockTransport(handler))

    assert client.channels("kb-1") == {"items": []}
    assert seen["url"] == "https://kms.example.test/channels?knowledge_base_id=kb-1"


def test_post_faqs_uses_json_body_with_pagination():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"items": []})

    client = KnowledgeClient(make_config(), token="abc", transport=httpx.MockTransport(handler))

    client.faqs("ch-1", page=2, page_size=50)

    assert '"channel_id":"ch-1"' in seen["body"]
    assert '"page":2' in seen["body"]
    assert '"page_size":50' in seen["body"]


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
