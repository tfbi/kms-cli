import json
from pathlib import Path
import sys

import httpx

from kms_cli.cli import main


CONFIG_TEXT = """
base_url = "https://kms.example.test"
token = "abc"

[endpoints.me]
method = "GET"
path = "/me"

[endpoints.knowledge_bases]
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


def test_knowledge_bases_sends_pagination(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"items": []})

    code = main(
        ["--config", str(config_path), "knowledge-bases", "--page", "3", "--page-size", "40"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert seen["body"] == {"page": 3, "page_size": 40}


def test_spaces_alias_still_sends_pagination(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"items": []})

    code = main(
        ["--config", str(config_path), "spaces", "--page", "3", "--page-size", "40"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert seen["body"] == {"page": 3, "page_size": 40}


def test_spaces_alias_works_from_process_argv(tmp_path, monkeypatch):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"items": []})

    monkeypatch.setattr(
        sys,
        "argv",
        ["kms", "--config", str(config_path), "spaces", "--page", "4", "--page-size", "30"],
    )

    code = main(transport=httpx.MockTransport(handler))

    assert code == 0
    assert seen["body"] == {"page": 4, "page_size": 30}


def test_help_promotes_knowledge_bases_command(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out
    assert "knowledge-bases" in output
    assert "spaces" not in output


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


def test_faqs_sends_channel_and_pagination(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"items": []})

    code = main(
        ["--config", str(config_path), "faqs", "ch-1", "--page", "2", "--page-size", "10"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert seen["body"] == {"channel_id": "ch-1", "page": 2, "page_size": 10}


def test_faq_detail_sends_query_parameter(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"id": "faq-1"})

    code = main(
        ["--config", str(config_path), "faq", "faq-1"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert seen["url"].endswith("/faq?faq_id=faq-1")


def test_auth_failure_prompts_for_new_token_and_retries(tmp_path):
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


def test_auth_failure_after_retry_returns_error(tmp_path, capsys):
    config_path = write_config(tmp_path)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "expired"})

    code = main(
        ["--config", str(config_path), "me", "--json"],
        transport=httpx.MockTransport(handler),
        input_func=lambda prompt: "new-token",
        confirm_func=lambda prompt: False,
    )

    assert code == 1
    assert "认证失败" in capsys.readouterr().err
