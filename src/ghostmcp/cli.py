"""GhostMCP command line.

    python -m ghostmcp servers --config <path>
    python -m ghostmcp tools --config <path> --server <name>
        [--timeout N]
    python -m ghostmcp call --config <path> --server <name>
        --tool <name> --args '<json object>' [--timeout N]

Every verb prints ONE JSON object to stdout. Failures print
``{"error": "..."}`` to stdout and exit 2 — including a tool
result the server marked ``isError`` is NOT a failure: it
prints normally with ``"isError": true`` and exits 0.
"""
from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .client import (DEFAULT_TIMEOUT, McpError, call_tool,
                     describe_servers, list_tools)


class _Parser(argparse.ArgumentParser):
    """ArgumentParser that reports usage errors the CLI way
    (one JSON object on stdout, exit 2) instead of argparse's
    stderr usage text."""

    def error(self, message):
        raise McpError(f"invalid command line: {message}")


def build_parser() -> argparse.ArgumentParser:
    parser = _Parser(
        prog="ghostmcp",
        description="MCP (Model Context Protocol) client for "
                    "GhostIDE (stdlib only).")
    parser.add_argument("--version", action="version",
                        version=f"ghostmcp {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p_servers = sub.add_parser(
        "servers", help="list the servers in a config file "
                        "(never connects, never prints env values)")
    p_servers.add_argument("--config", required=True,
                           help="path to the MCP config file")

    p_tools = sub.add_parser(
        "tools", help="list one server's tools")
    p_tools.add_argument("--config", required=True,
                         help="path to the MCP config file")
    p_tools.add_argument("--server", required=True,
                         help="server name from the config")
    p_tools.add_argument("--timeout", type=float,
                         default=DEFAULT_TIMEOUT,
                         help="seconds to allow for the whole "
                              "invocation (default 30)")

    p_call = sub.add_parser(
        "call", help="call one tool on one server")
    p_call.add_argument("--config", required=True,
                        help="path to the MCP config file")
    p_call.add_argument("--server", required=True,
                        help="server name from the config")
    p_call.add_argument("--tool", required=True,
                        help="tool name to call")
    p_call.add_argument("--args", required=True,
                        help="tool arguments as a JSON object")
    p_call.add_argument("--timeout", type=float,
                        default=DEFAULT_TIMEOUT,
                        help="seconds to allow for the whole "
                             "invocation (default 30)")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command == "servers":
            out = {"config": args.config,
                   "servers": describe_servers(args.config)}
        elif args.command == "tools":
            out = list_tools(args.config, args.server,
                             args.timeout)
        elif args.command == "call":
            out = call_tool(args.config, args.server, args.tool,
                            args.args, args.timeout)
        else:  # unreachable: argparse requires a verb
            raise McpError("no verb given")
    except McpError as e:
        print(json.dumps({"error": str(e)}))
        return 2
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
