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
    parser = argparse.ArgumentParser(prog="kms", add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH, help="配置文件路径")
    parser._positionals.title = "命令"
    parser._optionals.title = "选项"
    subparsers = parser.add_subparsers(dest="command", required=True)

    me = subparsers.add_parser("me", help="查询当前用户信息")
    me.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    knowledge_bases = subparsers.add_parser("knowledge-bases", help="分页获取知识库列表")
    _add_pagination(knowledge_bases)
    knowledge_bases.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    channels = subparsers.add_parser("channels", help="获取指定知识库下的渠道列表")
    channels.add_argument("knowledge_base_id", help="知识库 ID")
    channels.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    faqs = subparsers.add_parser("faqs", help="分页获取指定渠道下的 FAQ 列表")
    faqs.add_argument("channel_id", help="渠道 ID")
    _add_pagination(faqs)
    faqs.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    faq = subparsers.add_parser("faq", help="获取指定 FAQ 详情")
    faq.add_argument("faq_id", help="FAQ ID")
    faq.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    return parser


def main(
    argv: list[str] | None = None,
    *,
    transport: httpx.BaseTransport | None = None,
    input_func=None,
    confirm_func=None,
) -> int:
    parser = build_parser()
    raw_argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(_normalize_legacy_command(raw_argv))

    try:
        config = load_config(args.config)
        token_manager = TokenManager(config, input_func=input_func, confirm_func=confirm_func)
        with KnowledgeClient(config, token_manager.get_token(), transport=transport) as client:
            try:
                data = _execute(args, client)
            except AuthError:
                token = token_manager.refresh_token()
                with client.with_token(token) as refreshed_client:
                    data = _execute(args, refreshed_client)
    except KmsError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    print(_format(args, data))
    return 0


def _execute(args: argparse.Namespace, client: KnowledgeClient) -> dict[str, Any]:
    if args.command == "me":
        return client.me()
    if args.command == "knowledge-bases":
        return client.spaces(page=args.page, page_size=args.page_size)
    if args.command == "channels":
        return client.channels(args.knowledge_base_id)
    if args.command == "faqs":
        return client.faqs(args.channel_id, page=args.page, page_size=args.page_size)
    if args.command == "faq":
        return client.faq_detail(args.faq_id)
    raise AssertionError(f"未知命令: {args.command}")


def _format(args: argparse.Namespace, data: dict[str, Any]) -> str:
    if args.as_json:
        return format_json(data)
    if args.command == "me":
        return format_detail(data)
    if args.command == "knowledge-bases":
        return format_records(data, title="知识库")
    if args.command == "channels":
        return format_records(data, title="渠道")
    if args.command == "faqs":
        return format_records(data, title="FAQ")
    if args.command == "faq":
        return format_detail(data)
    raise AssertionError(f"未知命令: {args.command}")


def _add_pagination(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--page", type=int, default=1, help="页码")
    parser.add_argument("--page-size", type=int, default=20, help="每页数量")


def _normalize_legacy_command(argv: list[str]) -> list[str]:
    normalized = list(argv)
    skip_next = False
    for index, value in enumerate(normalized):
        if skip_next:
            skip_next = False
            continue
        if value == "--config":
            skip_next = True
            continue
        if value.startswith("--config="):
            continue
        if value == "spaces":
            normalized[index] = "knowledge-bases"
            break
        if not value.startswith("-"):
            break
    return normalized


if __name__ == "__main__":
    raise SystemExit(main())
