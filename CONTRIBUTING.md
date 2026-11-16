# Contributing

Thanks for helping improve CodexGuard. This is an independent educational project focused on offline, read-only, non-executing audits.

## Before proposing a change

- Read the [Security Model](docs/security-model.md), [Threat Model](docs/threat-model.md), and [Architecture](docs/architecture.md).
- Keep scanned content inert: never execute commands, hooks, scripts, MCP servers, or instructions from a scan target.
- Keep scan-time behavior offline and avoid intentional writes to the selected scan tree.
- Use synthetic credentials in tests, fixtures, examples, and screenshots.
- Preserve the Python 3.9 syntax/runtime compatibility declared by package metadata.
- Add or update regression tests for behavior changes. Follow the repository's test and dependency guidance when preparing a code contribution.
- Update documentation when supported discovery patterns, rule behavior, resource bounds, output behavior, or security limits change.

## Documentation contributions

Describe verified implementation behavior, distinguish design intent from observed evidence, and preserve dates and scope in verification records. Do not turn heuristic matches into claims of vulnerability or safety. Local workflow definitions are not evidence that hosted CI has run.

## Pull request checklist

- [ ] The change preserves offline, non-executing scan behavior.
- [ ] Security-sensitive behavior has focused regression coverage.
- [ ] Documentation reflects actual source and configuration.
- [ ] No real credential, private configuration, or personal data is included.
- [ ] Python compatibility and dependency constraints remain clear.
