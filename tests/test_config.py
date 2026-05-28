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
