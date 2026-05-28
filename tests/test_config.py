from pathlib import Path
import stat
import tomllib

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


def test_load_config_requires_string_base_url(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = 123

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

    with pytest.raises(ConfigError, match="base_url"):
        load_config(config_path)


def test_load_config_requires_string_token(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = "https://kms.example.test"
token = 123

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

    with pytest.raises(ConfigError, match="token"):
        load_config(config_path)


def test_load_config_wraps_file_read_errors(tmp_path):
    with pytest.raises(ConfigError, match="读取配置文件失败"):
        load_config(tmp_path)


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


def test_save_token_writes_config_with_private_permissions(tmp_path):
    config_path = tmp_path / ".kms" / "config.toml"

    save_token(config_path, "secret")

    assert stat.S_IMODE(config_path.stat().st_mode) == 0o600


def test_save_token_does_not_replace_nested_table_token(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = "https://kms.example.test"

[endpoints.me]
token = "nested"
method = "GET"
path = "/me"
""",
    )

    save_token(config_path, "root-token")

    text = config_path.read_text(encoding="utf-8")
    assert text.startswith('token = "root-token"\n')
    assert 'token = "nested"' in text


def test_save_token_escapes_control_characters_as_valid_toml(tmp_path):
    config_path = write_config(
        tmp_path / "config.toml",
        """
base_url = "https://kms.example.test"
token = "old"
""",
    )
    token = "line1\nline2\tend"

    save_token(config_path, token)

    raw = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert raw["token"] == token
