from __future__ import annotations

from types import TracebackType
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import KmsConfig
from .errors import AuthError, HttpRequestError, HttpStatusError, InvalidJsonError


class KnowledgeClient:
    def __init__(
        self,
        config: KmsConfig,
        token: str,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = 20.0,
    ) -> None:
        self.config = config
        self.token = token
        self.transport = transport
        self.timeout = timeout
        self._client = httpx.Client(transport=transport, timeout=timeout)

    def with_token(self, token: str) -> KnowledgeClient:
        return KnowledgeClient(
            self.config,
            token,
            transport=self.transport,
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> KnowledgeClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()

    def me(self) -> dict[str, Any]:
        return self._request("me")

    def spaces(self, *, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return self._request("spaces", json_body={"page": page, "page_size": page_size})

    def channels(self, knowledge_base_id: str) -> dict[str, Any]:
        return self._request("channels", params={"knowledge_base_id": knowledge_base_id})

    def faqs(self, channel_id: str, *, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        return self._request(
            "faqs",
            json_body={"channel_id": channel_id, "page": page, "page_size": page_size},
        )

    def faq_detail(self, faq_id: str) -> dict[str, Any]:
        return self._request("faq_detail", params={"faq_id": faq_id})

    def _request(
        self,
        endpoint_name: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        endpoint = self.config.endpoints[endpoint_name]
        url = _join_url(self.config.base_url, endpoint.path)
        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            response = self._client.request(
                endpoint.method,
                url,
                params=params,
                json=json_body,
                headers=headers,
            )
        except httpx.RequestError as exc:
            raise HttpRequestError(f"请求失败: {self.config.base_url} ({exc})") from exc

        if response.status_code in {401, 403}:
            raise AuthError("认证失败，token 可能已过期")
        if response.status_code < 200 or response.status_code >= 300:
            preview = response.text[:200]
            raise HttpStatusError(f"HTTP {response.status_code}: {preview}")

        try:
            data = response.json()
        except ValueError as exc:
            raise InvalidJsonError("接口返回内容不是合法 JSON") from exc
        if not isinstance(data, dict):
            raise InvalidJsonError("接口返回 JSON 顶层必须是对象")
        return data


def _join_url(base_url: str, path: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))
