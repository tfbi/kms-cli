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

    me = _add_subparser(subparsers, "me", help="查询当前用户信息")
    me.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    kbs = _add_subparser(subparsers, "kbs", help="分页获取知识库列表")
    _add_pagination(kbs)
    kbs.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    channels = _add_subparser(subparsers, "channels", help="获取指定知识库下的渠道列表")
    channels.add_argument("knowledge_id", metavar="knowledgeId", help="知识库 ID")
    channels.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    faqs = _add_subparser(subparsers, "faqs", help="分页获取指定渠道下的 FAQ 列表")
    faqs.add_argument("channel_id", metavar="channelId", help="渠道 ID")
    _add_pagination(faqs)
    faqs.add_argument("--json", action="store_true", dest="as_json", help="输出原始 JSON")

    faq = _add_subparser(subparsers, "faq", help="获取指定 FAQ 详情")
    faq.add_argument("faq_id", metavar="faqId", help="FAQ ID")
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
    args = parser.parse_args(argv)

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
    if args.command == "kbs":
        return client.kbs(page=args.page, page_size=args.page_size)
    if args.command == "channels":
        return client.channels(args.knowledge_id)
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
    if args.command == "kbs":
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


def _add_subparser(
    subparsers: argparse._SubParsersAction,
    name: str,
    *,
    help: str,
) -> argparse.ArgumentParser:
    parser = subparsers.add_parser(name, help=help, add_help=False)
    parser.add_argument("-h", "--help", action="help", help="显示帮助信息并退出")
    parser._positionals.title = "参数"
    parser._optionals.title = "选项"
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
