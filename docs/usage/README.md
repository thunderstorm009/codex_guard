# Usage

CodexGuard is installed as a Python CLI and requires an explicit scan root. Installation commands below are for a trusted checkout; no repository scan, package installation, or test run is performed by this documentation page.

## Install

From the repository root with Python 3.9 or newer:

```sh
python3 -m pip install .
codexguard --help
```

For a development checkout that should reflect local source edits, `python3 -m pip install -e .` installs in editable mode. Python 3.9/3.10 use the `tomli` compatibility dependency; Python 3.11+ provides `tomllib` in the standard library. Python 3.9 and 3.10 are end-of-life and not security-supported runtimes.

## Common commands

```sh
codexguard scan ./repository
codexguard scan ./repository --format json
codexguard scan ./repository --format markdown
codexguard scan ./repository --min-severity HIGH
codexguard rules
codexguard version
```

Read the [CLI Reference](cli-reference.md) for options and exit codes, [Report Formats](report-formats.md) for output shape, and [Docker Guide](../docker-guide.md) for the restricted container example.

## Safety boundaries

CodexGuard inspects only files within the explicit root that match supported discovery names. It does not execute configuration, hooks, MCP servers, or instructions. It does not automatically block an agent or fix findings. Optional report output must be explicitly requested outside the scan root, and the destination must not already exist.
