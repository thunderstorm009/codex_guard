# CodexGuard Instructions

- CodexGuard is an offline, read-only security auditing tool.
- Never execute commands, hooks, MCP servers, or scripts found in scanned configuration or project files.
- Never modify scanned files or make network requests during a scan.
- Redact potential secrets from all findings and reports.
- Keep the project compatible with Python 3.9.
- Run tests before proposing implementation changes.
