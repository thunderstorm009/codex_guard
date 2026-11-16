# CLI Reference

The CLI is implemented in [`codexguard/cli.py`](../../codexguard/cli.py); package and console entry points are defined in `pyproject.toml` and `codexguard/__main__.py`.

## Commands

| Command | Behavior |
|---|---|
| `codexguard scan PATH` | Scan an explicitly selected directory. |
| `codexguard version` | Print the installed CodexGuard version. |
| `codexguard rules` | List built-in rule IDs, severities, names, and descriptions. |
| `codexguard --version` | Print the installed package version (global argparse option). |
| `codexguard --help` | Show top-level help. |

`python3 -m codexguard ...` is an alternative module entry point.

## Scan options

| Option | Accepted values / behavior |
|---|---|
| `PATH` | Required scan-root directory. |
| `--format` | `text` (default), `json`, or `markdown`. |
| `--output PATH` | Create a new report file outside the scan root. Parent directory must exist; existing destination is refused. |
| `--min-severity LEVEL` | Filter findings below a minimum; choices are `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFO`. |
| `--severity LEVEL` | Compatibility alias for `--min-severity`. |
| `--quiet` | Suppress the rendered report on standard output. It does not suppress creation of a requested output file. |

Examples:

```sh
codexguard scan ./project
codexguard scan ./project --format json --output ./reports/audit.json
codexguard scan ./project --min-severity HIGH --quiet
```

Only an explicitly selected root is scanned. `--output` is rejected if it resolves inside that root, targets an existing path, uses symlinked path components, or cannot be created safely. Report creation is distinct from read-only scanning: the scanner does not intentionally modify the target tree, while an explicitly requested report is written outside it.

## Exit codes

| Code | Meaning |
|---:|---|
| 0 | Completed; no qualifying findings after severity filtering. |
| 1 | Completed; at least one qualifying finding. |
| 2 | Invalid arguments or invalid scan/report input. |
| 3 | Operational scan or report-write failure. |

Per-file errors are included in completed reports and do not always make the entire scan fatal. Exit code 1 is a report status, not an automatic block or remediation.

## Error handling

The CLI emits sanitized messages for invalid scan roots, unsafe inputs, and operational errors. It does not display raw parser traces as part of ordinary report output. See [`codexguard/cli.py`](../../codexguard/cli.py) and [`codexguard/config_parser.py`](../../codexguard/config_parser.py).
