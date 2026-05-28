from __future__ import annotations

from collections.abc import Callable
import getpass
import os

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
        token = _normalize_token(self._token)
        if token:
            self._token = token
            return token

        env_token = _normalize_token(os.getenv("KNOWLEDGE_TOKEN"))
        if env_token:
            self.source = "env"
            self._token = env_token
            return env_token

        config_token = _normalize_token(self.config.token)
        if config_token:
            self.source = "config"
            self._token = config_token
            return config_token

        token = self._prompt_token()
        self.source = "prompt"
        self._token = token
        return token

    def refresh_token(self) -> str:
        previous_source = self._resolve_source_for_refresh()

        token = self._prompt_token("认证已过期或无权限，请输入新的 token: ")
        self.source = "prompt"
        self._token = token
        if previous_source != "env" and self.confirm_func(
            "是否把新 token 保存到配置文件？[y/N]: "
        ):
            save_token(self.config.path, token)
        return token

    def _resolve_source_for_refresh(self) -> str:
        if self.source is not None:
            return self.source

        token = _normalize_token(self._token)
        if token:
            self._token = token
            return "prompt"

        env_token = _normalize_token(os.getenv("KNOWLEDGE_TOKEN"))
        if env_token:
            self.source = "env"
            self._token = env_token
            return "env"

        config_token = _normalize_token(self.config.token)
        if config_token:
            self.source = "config"
            self._token = config_token
            return "config"

        return "prompt"

    def _prompt_token(self, prompt: str = "请输入 token: ") -> str:
        token = _normalize_token(self.input_func(prompt))
        if not token:
            raise AuthError("token 不能为空")
        return token


def _normalize_token(value: str | None) -> str | None:
    if value is None:
        return None
    token = value.strip()
    return token or None


def _confirm_yes(prompt: str) -> bool:
    answer = input(prompt).strip().lower()
    return answer in {"y", "yes"}
