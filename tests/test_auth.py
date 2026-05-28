from pathlib import Path
import tomllib

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
    monkeypatch.setenv("KNOWLEDGE_TOKEN", "  env-token  ")
    manager = TokenManager(make_config(tmp_path), input_func=lambda _: "prompt-token")

    assert manager.get_token() == "env-token"
    assert manager.source == "env"


def test_config_token_used_when_env_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    manager = TokenManager(make_config(tmp_path, token="  config-token  "))

    assert manager.get_token() == "config-token"
    assert manager.source == "config"


def test_whitespace_environment_token_falls_back_to_config(monkeypatch, tmp_path):
    monkeypatch.setenv("KNOWLEDGE_TOKEN", "   ")
    manager = TokenManager(make_config(tmp_path, token="config-token"))

    assert manager.get_token() == "config-token"
    assert manager.source == "config"


def test_whitespace_config_token_falls_back_to_prompt(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    manager = TokenManager(
        make_config(tmp_path, token="   "),
        input_func=lambda prompt: "manual-token",
    )

    assert manager.get_token() == "manual-token"
    assert manager.source == "prompt"


def test_prompts_when_no_token(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    manager = TokenManager(
        make_config(tmp_path, token=None),
        input_func=lambda prompt: "  manual-token  ",
    )

    assert manager.get_token() == "manual-token"
    assert manager.source == "prompt"


def test_refresh_updates_current_token_without_printing_old_token(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    prompts: list[str] = []

    def capture_prompt(prompt: str) -> str:
        prompts.append(prompt)
        return "new-token"

    manager = TokenManager(
        make_config(tmp_path, token="old-token"),
        input_func=capture_prompt,
        confirm_func=lambda prompt: False,
    )

    assert manager.refresh_token() == "new-token"
    assert manager.get_token() == "new-token"
    assert prompts
    assert "old-token" not in prompts[0]


def test_refresh_skips_persistence_when_current_token_source_is_env(monkeypatch, tmp_path):
    monkeypatch.setenv("KNOWLEDGE_TOKEN", "env-token")
    config_path = tmp_path / "config.toml"
    config_path.write_text('base_url = "https://kms.example.test"\n', encoding="utf-8")

    def fail_if_called(prompt: str) -> bool:
        raise AssertionError("confirm_func should not be called for env token refresh")

    manager = TokenManager(
        make_config(tmp_path, token="config-token"),
        input_func=lambda prompt: "new-token",
        confirm_func=fail_if_called,
    )

    assert manager.get_token() == "env-token"
    assert manager.refresh_token() == "new-token"
    assert manager.get_token() == "new-token"
    assert "token" not in tomllib.loads(config_path.read_text(encoding="utf-8"))


def test_refresh_persists_new_token_when_confirmed(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    config_path = tmp_path / "config.toml"
    config_path.write_text('base_url = "https://kms.example.test"\n', encoding="utf-8")
    manager = TokenManager(
        make_config(tmp_path, token="old-token"),
        input_func=lambda prompt: "new-token",
        confirm_func=lambda prompt: True,
    )

    assert manager.refresh_token() == "new-token"

    parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert parsed["token"] == "new-token"


def test_refresh_before_get_token_with_prompt_source_prompts_once(monkeypatch, tmp_path):
    monkeypatch.delenv("KNOWLEDGE_TOKEN", raising=False)
    config_path = tmp_path / "config.toml"
    config_path.write_text('base_url = "https://kms.example.test"\n', encoding="utf-8")
    prompts: list[str] = []
    manager = TokenManager(
        make_config(tmp_path, token=None),
        input_func=lambda prompt: prompts.append(prompt) or "new-token",
        confirm_func=lambda prompt: True,
    )

    assert manager.refresh_token() == "new-token"
    assert prompts == ["Token 已过期或无权限，请输入新的 token: "]

    parsed = tomllib.loads(config_path.read_text(encoding="utf-8"))
    assert parsed["token"] == "new-token"
