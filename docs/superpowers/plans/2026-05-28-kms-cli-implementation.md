# KMS CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python CLI named `kms` that reads config/token, calls internal knowledge-center HTTP endpoints, supports token refresh, and exposes the five approved commands.

**Architecture:** The package is split into focused modules: config loading, auth/token handling, HTTP client, output formatting, and CLI command wiring. Tests drive each behavior with temporary config files and mocked HTTP transports so no real internal service is called.

**Tech Stack:** Python 3.11+, `argparse`, `httpx`, `pytest`, `httpx.MockTransport`.

---

## File Structure

- `pyproject.toml`: package metadata, console script entry point, test dependencies.
- `README.md`: quick setup, config example, and command examples.
- `src/kms_cli/__init__.py`: package marker and version.
- `src/kms_cli/errors.py`: typed exceptions used across the package.
- `src/kms_cli/config.py`: TOML config loading, validation, token persistence.
- `src/kms_cli/auth.py`: token resolution and refresh prompt flow.
- `src/kms_cli/client.py`: `KnowledgeClient` and HTTP request behavior.
- `src/kms_cli/formatters.py`: human-readable and JSON output formatting.
- `src/kms_cli/cli.py`: `argparse` commands and command execution.
- `tests/test_config.py`: config validation and token persistence tests.
- `tests/test_auth.py`: token priority and refresh prompt tests.
- `tests/test_client.py`: GET query, POST body, auth failure, and HTTP error tests.
- `tests/test_cli.py`: CLI dispatch and output tests.

---

### Task 1: Package Skeleton

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/kms_cli/__init__.py`
- Create: `src/kms_cli/errors.py`
- Create: `tests/test_imports.py`

- [ ] **Step 1: Write the failing import test**

Create `tests/test_imports.py`:

```python
def test_package_exposes_version():
    import kms_cli

    assert isinstance(kms_cli.__version__, str)
    assert kms_cli.__version__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_imports.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'kms_cli'`.

- [ ] **Step 3: Add package metadata and minimal package**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "kms-cli"
version = "0.1.0"
description = "Internal knowledge center CLI"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.27",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
]

[project.scripts]
kms = "kms_cli.cli:main"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `src/kms_cli/__init__.py`:

```python
__version__ = "0.1.0"
```

Create `src/kms_cli/errors.py`:

```python
class KmsError(Exception):
    """Base error for user-facing KMS CLI failures."""


class ConfigError(KmsError):
    """Raised when local CLI configuration is missing or invalid."""


class AuthError(KmsError):
    """Raised when authentication is missing, expired, or rejected."""


class HttpRequestError(KmsError):
    """Raised when an HTTP request fails before receiving a response."""


class HttpStatusError(KmsError):
    """Raised when the service returns a non-success response."""


class InvalidJsonError(KmsError):
    """Raised when the service returns a body that is not valid JSON."""
```

Create `README.md` with a short usage outline:

```markdown
# KMS CLI

Python CLI for an internal knowledge center.

## Commands

- `kms me`
- `kms spaces`
- `kms channels <knowledge_base_id>`
- `kms faqs <channel_id>`
- `kms faq <faq_id>`
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_imports.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md src/kms_cli/__init__.py src/kms_cli/errors.py tests/test_imports.py
git commit -m "feat: add kms cli package skeleton"
```

---

### Task 2: Config Loading

**Files:**
- Create: `src/kms_cli/config.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write failing config tests**

Create `tests/test_config.py`:

```python
from pathlib import Path

import pytest

from kms_cli.config import EndpointConfig, KmsConfig, load_config, save_token
from kms_cli.errors import ConfigError


def write_config(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_config_reads_required_fields(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = "https://kms.example.test"
token = "abc"

[endpoints.me]
method = "GET"
path = "/me"

[endpoints.spaces]
method = "POST"
path = "/spaces"

[endpoints.channels]
method = "GET"
path = "/channels"

[endpoints.faqs]
method = "POST"
path = "/faqs"

[endpoints.faq_detail]
method = "GET"
path = "/faq"
""",
    )

    config = load_config(config_path)

    assert config == KmsConfig(
        base_url="https://kms.example.test",
        token="abc",
        endpoints={
            "me": EndpointConfig(method="GET", path="/me"),
            "spaces": EndpointConfig(method="POST", path="/spaces"),
            "channels": EndpointConfig(method="GET", path="/channels"),
            "faqs": EndpointConfig(method="POST", path="/faqs"),
            "faq_detail": EndpointConfig(method="GET", path="/faq"),
        },
        path=config_path,
    )


def test_load_config_reports_missing_file(tmp_path):
    with pytest.raises(ConfigError, match="配置文件不存在"):
        load_config(tmp_path / "missing.toml")


def test_load_config_requires_all_endpoints(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = "https://kms.example.test"

[endpoints.me]
method = "GET"
path = "/me"
""",
    )

    with pytest.raises(ConfigError, match="缺少接口配置"):
        load_config(config_path)


def test_save_token_updates_existing_config(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = "https://kms.example.test"
token = "old"

[endpoints.me]
method = "GET"
path = "/me"

[endpoints.spaces]
method = "POST"
path = "/spaces"

[endpoints.channels]
method = "GET"
path = "/channels"

[endpoints.faqs]
method = "POST"
path = "/faqs"

[endpoints.faq_detail]
method = "GET"
path = "/faq"
""",
    )

    save_token(config_path, "new-token")

    assert 'token = "new-token"' in config_path.read_text(encoding="utf-8")
    assert 'token = "old"' not in config_path.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`

Expected: FAIL because `kms_cli.config` does not exist.

- [ ] **Step 3: Implement config module**

Create `src/kms_cli/config.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import tomllib

from .errors import ConfigError

DEFAULT_CONFIG_PATH = Path.home() / ".kms" / "config.toml"
REQUIRED_ENDPOINTS = ("me", "spaces", "channels", "faqs", "faq_detail")


@dataclass(frozen=True)
class EndpointConfig:
    method: str
    path: str


@dataclass(frozen=True)
class KmsConfig:
    base_url: str
    token: str | None
    endpoints: dict[str, EndpointConfig]
    path: Path


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> KmsConfig:
    if not path.exists():
        raise ConfigError(f"配置文件不存在: {path}")

    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"配置文件格式错误: {exc}") from exc

    base_url = str(raw.get("base_url", "")).strip()
    if not base_url:
        raise ConfigError("缺少必填配置: base_url")

    raw_endpoints = raw.get("endpoints")
    if not isinstance(raw_endpoints, dict):
        raise ConfigError("缺少接口配置: endpoints")

    endpoints: dict[str, EndpointConfig] = {}
    for name in REQUIRED_ENDPOINTS:
        item = raw_endpoints.get(name)
        if not isinstance(item, dict):
            raise ConfigError(f"缺少接口配置: endpoints.{name}")
        method = str(item.get("method", "")).upper().strip()
        endpoint_path = str(item.get("path", "")).strip()
        if method not in {"GET", "POST"}:
            raise ConfigError(f"接口 endpoints.{name}.method 只支持 GET 或 POST")
        if not endpoint_path.startswith("/"):
            raise ConfigError(f"接口 endpoints.{name}.path 必须以 / 开头")
        endpoints[name] = EndpointConfig(method=method, path=endpoint_path)

    token = raw.get("token")
    return KmsConfig(
        base_url=base_url.rstrip("/"),
        token=str(token) if token else None,
        endpoints=endpoints,
        path=path,
    )


def save_token(path: Path, token: str) -> None:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    token_line = f'token = "{_escape_toml_string(token)}"'
    if re.search(r'^token\s*=\s*".*"$', text, flags=re.MULTILINE):
        text = re.sub(r'^token\s*=\s*".*"$', token_line, text, flags=re.MULTILINE)
    else:
        text = token_line + "\n" + text
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _escape_toml_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/kms_cli/config.py tests/test_config.py
git commit -m "feat: load kms cli config"
```

---

### Task 3: Auth Token Handling

**Files:**
- Create: `src/kms_cli/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: Write failing auth tests**

Create `tests/test_auth.py`:

```python
from pathlib import Path

from kms_cli.auth import TokenManager
from kms_cli.config import KmsConfig


def make_config(tmp_path: Path, token: str | None = "config-token") -> KmsConfig:
    return KmsConfig(
        base_url="https://kms.example.test",
        token=token,
        endpoints={},
        path=tmp_path / "config.toml",
    )


def test_environment_token_wins(monkeypatch, tmp_path):
    monkeypatch.setenv("KNOWLEDGE_TOKEN", "env-token")
    manager = TokenManager(make_config(tmp_path), input_func=lambda _: "prompt-token")

    assert manager.get_token() == "env-token"
    assert manager.source == "env"


def test_config_token_used_when_env_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    manager = TokenManager(make_config(tmp_path, token="config-token"))

    assert manager.get_token() == "config-token"
    assert manager.source == "config"


def test_prompts_when_no_token(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    manager = TokenManager(
        make_config(tmp_path, token=None),
        input_func=lambda prompt: "manual-token",
    )

    assert manager.get_token() == "manual-token"
    assert manager.source == "prompt"


def test_refresh_updates_current_token_without_printing_old_token(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    manager = TokenManager(
        make_config(tmp_path, token="old-token"),
        input_func=lambda prompt: "new-token",
        confirm_func=lambda prompt: False,
    )

    assert manager.refresh_token() == "new-token"
    assert manager.get_token() == "new-token"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_auth.py -v`

Expected: FAIL because `kms_cli.auth` does not exist.

- [ ] **Step 3: Implement token manager**

Create `src/kms_cli/auth.py`:

```python
from __future__ import annotations

import getpass
import os
from collections.abc import Callable

from .config import KmsConfig, save_token
from .errors import AuthError


class TokenManager:
    def __init__(
        self,
        config: KmsConfig,
        *,
        input_func: Callable[[str], str] | None = None,
        confirm_func: Callable[[str], bool] | None = None,
    ) -> None:
        self.config = config
        self.input_func = input_func or getpass.getpass
        self.confirm_func = confirm_func or _confirm_yes
        self.source: str | None = None
        self._token: str | None = None

    def get_token(self) -> str:
        if self._token:
            return self._token

        env_token = os.getenv("KNOWLEDGE_TOKEN")
        if env_token:
            self.source = "env"
            self._token = env_token
            return env_token

        if self.config.token:
            self.source = "config"
            self._token = self.config.token
            return self.config.token

        token = self._prompt_token()
        self.source = "prompt"
        self._token = token
        return token

    def refresh_token(self) -> str:
        token = self._prompt_token("Token 已过期或无权限，请输入新的 token: ")
        self.source = "prompt"
        self._token = token
        if self.confirm_func("是否把新 token 保存到配置文件？[y/N]: "):
            save_token(self.config.path, token)
        return token

    def _prompt_token(self, prompt: str = "请输入 token: ") -> str:
        token = self.input_func(prompt).strip()
        if not token:
            raise AuthError("token 不能为空")
        return token


def _confirm_yes(prompt: str) -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_auth.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/kms_cli/auth.py tests/test_auth.py
git commit -m "feat: resolve and refresh kms token"
```

---

### Task 4: HTTP Client

**Files:**
- Create: `src/kms_cli/client.py`
- Create: `tests/test_client.py`

- [ ] **Step 1: Write failing client tests**

Create `tests/test_client.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_client.py -v`

Expected: FAIL because `kms_cli.client` does not exist.

- [ ] **Step 3: Implement `KnowledgeClient`**

Create `src/kms_cli/client.py`:

```python
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import httpx

from .config import EndpointConfig, KmsConfig
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
        self._client = httpx.Client(transport=transport, timeout=timeout)

    def with_token(self, token: str) -> "KnowledgeClient":
        return KnowledgeClient(self.config, token)

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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_client.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/kms_cli/client.py tests/test_client.py
git commit -m "feat: add kms knowledge client"
```

---

### Task 5: Output Formatters

**Files:**
- Create: `src/kms_cli/formatters.py`
- Create: `tests/test_formatters.py`

- [ ] **Step 1: Write failing formatter tests**

Create `tests/test_formatters.py`:

```python
import json

from kms_cli.formatters import format_json, format_records, format_detail


def test_format_json_keeps_non_ascii_text():
    assert format_json({"name": "知识库"}) == '{\n  "name": "知识库"\n}'


def test_format_records_uses_common_id_and_name_fields():
    text = format_records({"items": [{"id": "1", "name": "渠道 A"}]}, title="渠道")

    assert "渠道" in text
    assert "1" in text
    assert "渠道 A" in text


def test_format_detail_renders_nested_json_readably():
    text = format_detail({"id": "faq-1", "title": "问题", "answer": "答案"})

    assert '"faq-1"' in text
    assert '"问题"' in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_formatters.py -v`

Expected: FAIL because `kms_cli.formatters` does not exist.

- [ ] **Step 3: Implement formatters**

Create `src/kms_cli/formatters.py`:

```python
from __future__ import annotations

import json
from typing import Any


def format_json(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def format_detail(data: dict[str, Any]) -> str:
    return format_json(data)


def format_records(data: dict[str, Any], *, title: str) -> str:
    records = _extract_records(data)
    if not records:
        return f"{title}: 无数据"

    lines = [f"{title}:"]
    for record in records:
        if isinstance(record, dict):
            record_id = _pick(record, "id", "faq_id", "channel_id", "knowledge_base_id")
            name = _pick(record, "name", "title")
            if record_id and name:
                lines.append(f"- {record_id}\t{name}")
            elif name:
                lines.append(f"- {name}")
            else:
                lines.append(f"- {format_json(record)}")
        else:
            lines.append(f"- {record}")
    return "\n".join(lines)


def _extract_records(data: dict[str, Any]) -> list[Any]:
    for key in ("items", "records", "data", "list"):
        value = data.get(key)
        if isinstance(value, list):
            return value
        if isinstance(value, dict):
            nested = _extract_records(value)
            if nested:
                return nested
    return []


def _pick(record: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = record.get(key)
        if value is not None:
            return str(value)
    return ""
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_formatters.py -v`

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/kms_cli/formatters.py tests/test_formatters.py
git commit -m "feat: format kms cli output"
```

---

### Task 6: CLI Commands and Auth Retry

**Files:**
- Create: `src/kms_cli/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli.py`:

```python
from pathlib import Path

import httpx
import pytest

from kms_cli.cli import main


CONFIG_TEXT = """
base_url = "https://kms.example.test"
token = "abc"

[endpoints.me]
method = "GET"
path = "/me"

[endpoints.spaces]
method = "POST"
path = "/spaces"

[endpoints.channels]
method = "GET"
path = "/channels"

[endpoints.faqs]
method = "POST"
path = "/faqs"

[endpoints.faq_detail]
method = "GET"
path = "/faq"
"""


def write_config(tmp_path: Path) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(CONFIG_TEXT, encoding="utf-8")
    return path


def test_me_outputs_json(tmp_path, capsys):
    config_path = write_config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "u1", "name": "张三"})

    code = main(
        ["--config", str(config_path), "me", "--json"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert '"张三"' in capsys.readouterr().out


def test_spaces_sends_pagination(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"items": []})

    code = main(
        ["--config", str(config_path), "spaces", "--page", "3", "--page-size", "40"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert '"page":3' in seen["body"]
    assert '"page_size":40' in seen["body"]


def test_channels_sends_query_parameter(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"items": []})

    code = main(
        ["--config", str(config_path), "channels", "kb-1"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert seen["url"].endswith("/channels?knowledge_base_id=kb-1")


def test_auth_failure_prompts_for_new_token_and_retries(tmp_path, capsys):
    config_path = write_config(tmp_path)
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.headers["Authorization"])
        if len(calls) == 1:
            return httpx.Response(401, json={"error": "expired"})
        return httpx.Response(200, json={"id": "u1"})

    code = main(
        ["--config", str(config_path), "me", "--json"],
        transport=httpx.MockTransport(handler),
        input_func=lambda prompt: "new-token",
        confirm_func=lambda prompt: False,
    )

    assert code == 0
    assert calls == ["Bearer abc", "Bearer new-token"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`

Expected: FAIL because `kms_cli.cli` does not exist.

- [ ] **Step 3: Implement CLI**

Create `src/kms_cli/cli.py`:

```python
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import httpx

from .auth import TokenManager
from .client import KnowledgeClient
from .config import DEFAULT_CONFIG_PATH, load_config
from .errors import AuthError, KmsError
from .formatters import format_detail, format_json, format_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kms")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="配置文件路径")
    subparsers = parser.add_subparsers(dest="command", required=True)

    me = subparsers.add_parser("me", help="查询当前用户信息")
    me.add_argument("--json", action="store_true", dest="as_json")

    spaces = subparsers.add_parser("spaces", help="分页获取知识库列表")
    _add_pagination(spaces)
    spaces.add_argument("--json", action="store_true", dest="as_json")

    channels = subparsers.add_parser("channels", help="获取指定知识库下的渠道列表")
    channels.add_argument("knowledge_base_id")
    channels.add_argument("--json", action="store_true", dest="as_json")

    faqs = subparsers.add_parser("faqs", help="分页获取指定渠道下的 FAQ 列表")
    faqs.add_argument("channel_id")
    _add_pagination(faqs)
    faqs.add_argument("--json", action="store_true", dest="as_json")

    faq = subparsers.add_parser("faq", help="获取指定 FAQ 详情")
    faq.add_argument("faq_id")
    faq.add_argument("--json", action="store_true", dest="as_json")

    return parser


def main(
    argv: list[str] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
    input_func=None,
    confirm_func=None,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        token_manager = TokenManager(config, input_func=input_func, confirm_func=confirm_func)
        client = KnowledgeClient(config, token_manager.get_token(), transport=transport)
        data = _execute(args, client)
    except AuthError:
        try:
            token = token_manager.refresh_token()  # type: ignore[has-type]
            client = KnowledgeClient(config, token, transport=transport)  # type: ignore[has-type]
            data = _execute(args, client)
        except KmsError as exc:
            print(f"错误: {exc}", file=sys.stderr)
            return 1
    except KmsError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print(_format(args, data))
    return 0


def _execute(args: argparse.Namespace, client: KnowledgeClient) -> dict[str, Any]:
    if args.command == "me":
        return client.me()
    if args.command == "spaces":
        return client.spaces(page=args.page, page_size=args.page_size)
    if args.command == "channels":
        return client.channels(args.knowledge_base_id)
    if args.command == "faqs":
        return client.faqs(args.channel_id, page=args.page, page_size=args.page_size)
    if args.command == "faq":
        return client.faq_detail(args.faq_id)
    raise AssertionError(f"unknown command: {args.command}")


def _format(args: argparse.Namespace, data: dict[str, Any]) -> str:
    if args.as_json:
        return format_json(data)
    if args.command == "me":
        return format_detail(data)
    if args.command == "spaces":
        return format_records(data, title="知识库")
    if args.command == "channels":
        return format_records(data, title="渠道")
    if args.command == "faqs":
        return format_records(data, title="FAQ")
    if args.command == "faq":
        return format_detail(data)
    raise AssertionError(f"unknown command: {args.command}")


def _add_pagination(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--page-size", type=int, default=20)


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`

Expected: PASS.

- [ ] **Step 5: Run full test suite**

Run: `pytest -v`

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/kms_cli/cli.py tests/test_cli.py
git commit -m "feat: add kms cli commands"
```

---

### Task 7: Documentation and Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README with complete usage**

Replace `README.md` with:

````markdown
# KMS CLI

Python CLI for an internal knowledge center.

## Install for local development

```bash
python -m pip install -e ".[dev]"
```

## Config

Create `~/.kms/config.toml`:

```toml
base_url = "https://internal.example.com"
token = "..."

[endpoints.me]
method = "GET"
path = "/api/me"

[endpoints.spaces]
method = "POST"
path = "/api/knowledge-bases"

[endpoints.channels]
method = "GET"
path = "/api/channels"

[endpoints.faqs]
method = "POST"
path = "/api/faqs"

[endpoints.faq_detail]
method = "GET"
path = "/api/faq/detail"
```

`KNOWLEDGE_TOKEN` overrides the token stored in the config file.

## Commands

```bash
kms me
kms spaces --page 1 --page-size 20
kms channels <knowledge_base_id>
kms faqs <channel_id> --page 1 --page-size 20
kms faq <faq_id>
```

Add `--json` to any command to print raw JSON.
````

- [ ] **Step 2: Run final verification**

Run: `pytest -v`

Expected: PASS.

Run: `python -m kms_cli.cli --help`

Expected: exits 0 and shows `kms` commands.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document kms cli usage"
```

---

## Self-Review

Spec coverage:

- `kms me`, `kms spaces`, `kms channels`, `kms faqs`, and `kms faq` are implemented in Task 6.
- Config-driven `base_url`, endpoint method, and endpoint path are implemented in Task 2 and used in Task 4.
- Environment-token priority, config token fallback, interactive token input, token refresh, and optional persistence are implemented in Task 3 and exercised through Task 6.
- POST pagination for knowledge base and FAQ list calls is implemented in Task 4 and tested in Tasks 4 and 6.
- GET query parameters for channel list and FAQ detail are implemented in Task 4.
- JSON and human-readable output are implemented in Task 5 and wired in Task 6.
- Error handling for missing config, auth failure, HTTP status failure, request failure, and invalid JSON is implemented across Tasks 2, 4, and 6.

Placeholder scan:

- No placeholder markers remain.
- No path-template parameters are used for GET requests.
- No real internal endpoints or tokens are embedded.

Type consistency:

- Config endpoint names are consistently `me`, `spaces`, `channels`, `faqs`, and `faq_detail`.
- Public client methods are consistently `me`, `spaces`, `channels`, `faqs`, and `faq_detail`.
- CLI command names are consistently `me`, `spaces`, `channels`, `faqs`, and `faq`.
