"""Command-line interface for NepTLS."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from . import __version__, get, profiles, ua
from .crypto import blake2, md5, sha256, sha512
from .diagnostics import inspect
from .pow import Challenge, solve


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="neptls", description="NepTLS networking research toolkit")
    sub = parser.add_subparsers(dest="command")
    for method in ("get", "post", "put", "patch", "delete", "head", "options"):
        command = sub.add_parser(method, help=f"perform an HTTP {method.upper()} request")
        command.add_argument("url")
        command.add_argument("--json", dest="json_body", help="JSON request body")
        command.add_argument("--header", action="append", default=[], metavar="NAME:VALUE")
    for name in ("inspect", "diagnose"):
        command = sub.add_parser(name, help="inspect DNS, TCP, TLS, and HTTP")
        command.add_argument("url")
        command.add_argument("--json", action="store_true", dest="as_json")
    sub.add_parser("version")
    profile_command = sub.add_parser("profile", help="list browser profiles")
    profile_command.add_argument("name", nargs="?")
    ua_command = sub.add_parser("ua", help="query the user-agent catalog")
    ua_command.add_argument("kind", nargs="?", default="random", choices=("random", "chrome", "firefox", "mobile"))
    hash_command = sub.add_parser("hash", help="hash text")
    hash_command.add_argument("value")
    hash_command.add_argument("--algorithm", choices=("sha256", "sha512", "blake2", "md5"), default="sha256")
    pow_command = sub.add_parser("pow", help="solve a generic proof-of-work challenge")
    pow_command.add_argument("payload")
    pow_command.add_argument("--difficulty", type=int, default=4)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "version":
        print(__version__)
        return 0
    if args.command in {"get", "post", "put", "patch", "delete", "head", "options"}:
        headers = dict(item.split(":", 1) for item in args.header if ":" in item)
        body = json.loads(args.json_body) if args.json_body else None
        response = getattr(__import__("neptls"), args.command)(args.url, headers=headers, json=body)
        print(response.text)
        return 0 if response.ok else 1
    if args.command in {"inspect", "diagnose"}:
        print(json.dumps(inspect(args.url), indent=2, default=str))
        return 0
    if args.command == "profile":
        value = profiles.PROFILES if not args.name else profiles.get_profile(args.name).to_dict()
        print(json.dumps(value, indent=2, default=str))
        return 0
    if args.command == "ua":
        print(getattr(ua, args.kind)())
        return 0
    if args.command == "hash":
        function = {"sha256": sha256, "sha512": sha512, "blake2": blake2, "md5": md5}[args.algorithm]
        print(function(args.value))
        return 0
    if args.command == "pow":
        result = solve(Challenge(args.payload, difficulty=args.difficulty))
        print(json.dumps(asdict(result), default=str))
        return 0
    _parser().print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
