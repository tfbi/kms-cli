from __future__ import annotations

from dataclasses import dataclass
import json
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
    token_line = f"token = {_escape_toml_string(token)}"
    lines = text.splitlines(keepends=True)
    root_token_updated = False

    for index, line in enumerate(lines):
        if line.lstrip().startswith("["):
            break
        if re.match(r"^\s*token\s*=", line):
            line_ending = "\n" if line.endswith("\n") else ""
            lines[index] = token_line + line_ending
            text = "".join(lines)
            root_token_updated = True
            break
    if not root_token_updated:
        text = token_line + "\n" + text

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _escape_toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)
