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
