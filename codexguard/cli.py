"""Command-line interface for offline CodexGuard audits."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence

from . import __version__
from .config_parser import ConfigInputError
from .constants import APP_NAME, SUPPORTED_FORMATS
from .reporter import ReportWriteError, render, write_report
from .rules import load_rules, SEVERITIES
from .scanner import filter_findings, scan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="codexguard", description="Offline, read-only Codex security audit")
    parser.add_argument("--version", action="version", version="{} {}".format(APP_NAME, __version__))
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version", help="show the installed CodexGuard version")
    subparsers.add_parser("rules", help="list the built-in heuristic rules")
    scan_parser = subparsers.add_parser("scan", help="scan an explicitly selected directory")
    scan_parser.add_argument("scan_root", type=Path)
    scan_parser.add_argument("--format", choices=SUPPORTED_FORMATS, default="text")
    scan_parser.add_argument("--output", type=Path, help="write report outside the scanned directory")
    scan_parser.add_argument(
        "--min-severity", "--severity", dest="severity", choices=SEVERITIES,
        help="minimum severity to report and fail on",
    )
    scan_parser.add_argument("--quiet", action="store_true", help="do not print the report to the terminal")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "version":
        print("{} {}".format(APP_NAME, __version__))
        return 0
    if args.command == "rules":
        for rule in load_rules():
            print("{} [{}] {}: {}".format(rule.rule_id, rule.severity, rule.name, rule.description))
        return 0
    try:
        result = scan(args.scan_root)
        result.findings = filter_findings(result.findings, args.severity)
        content = render(result, args.format)
        if args.output:
            write_report(content, args.output, Path(result.scan_root_path or result.scan_root))
        if not args.quiet:
            print(content, end="")
        return 1 if result.findings else 0
    except ConfigInputError as exc:
        print("CodexGuard: {}".format(exc.message), file=sys.stderr)
        return 2 if exc.code == "invalid_scan_root" else 3
    except ReportWriteError:
        print("CodexGuard: report or scan operation could not be completed safely", file=sys.stderr)
        return 3
    except ValueError:
        print("CodexGuard: invalid scan or report input", file=sys.stderr)
        return 2
    except OSError:
        print("CodexGuard: scan could not be completed safely", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
