import json
from pathlib import Path

import httpx

from kms_cli.cli import main


CONFIG_TEXT = """
base_url = "https://kms.example.test"
token = "abc"

[endpoints.me]
method = "GET"
path = "/me"

[endpoints.kbs]
method = "POST"
path = "/kbs"

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


def test_kbs_sends_pagination(tmp_path):
    config_path = write_config(tmp_path)
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"items": []})

    code = main(
        ["--config", str(config_path), "kbs", "--page", "3", "--page-size", "40"],
        transport=httpx.MockTransport(handler),
    )

    assert code == 0
    assert seen["body"] == {"pageNo": 3, "pageSize": 40}


def test_help_promotes_kbs_command(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out
    assert "kbs" in output
    assert "knowledge-bases" not in output
    assert "spaces" not in output


def test_subcommand_help_uses_chinese_labels(capsys):
    try:
        main(["channels", "--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out
    assert "参数:" in output
    assert "选项:" in output
    assert "显示帮助信息并退出" in output
    assert "knowledgeId" in output


def test_old_knowledge_base_commands_are_not_supported(tmp_path):
    config_path = write_config(tmp_path)

    for command in ("knowledge-bases", "spaces"):
        try:
            main(["--config", str(config_path), command])
        except SystemExit as exc:
            assert exc.code == 2
        else:
            raise AssertionError(f"旧命令应该不可用: {command}")


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
    assert seen["url"].endswith("/channels?knowledgeId=kb-1")


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
    assert seen["body"] == {"channelId": "ch-1", "pageNo": 2, "pageSize": 10}


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
    assert seen["url"].endswith("/faq?faqId=faq-1")


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
