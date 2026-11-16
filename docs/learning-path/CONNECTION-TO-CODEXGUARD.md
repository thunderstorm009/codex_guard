# How the Learning Path Connects to CodexGuard

CodexGuard is an applied project that combines agent-aware threat modeling, secure file handling, rule-based analysis, human review, and container isolation. The table below maps the learning topics to specific code and documentation so the relationship stays concrete.

| Learning topic | CodexGuard implementation | What the project demonstrates |
|---|---|---|
| Coding-agent context | `AGENTS.md`, `.codex/config.toml`, `codexguard/rules.py` | Repository content can influence agent behavior, so review it as untrusted input. |
| Agent/tool permissions | CG-001, CG-002, CG-003, CG-006 | Configuration and hooks can merit review; a match is a prompt for a person, not proof of an exploit. |
| Offline, bounded inspection | `codexguard/scanner.py`, `codexguard/constants.py` | Explicit roots, fixed candidate patterns, descriptor-based traversal, and finite limits reduce exposure. |
| Parsing as data | `codexguard/config_parser.py` | TOML is decoded into values; configured commands and instructions are not run. |
| Detection and privacy | `codexguard/rules.py`, `codexguard/security_rules.json` | Narrow heuristics and secret redaction provide useful evidence while leaving coverage limits visible. |
| Human oversight | `codexguard/reporter.py`, CLI exit codes | Findings, context, confidence, and recommendations support review; the tool does not block Codex or auto-fix files. |
| Container boundaries | `docker/Dockerfile`, `docs/docker-guide.md` | Non-root identity is configured in the image; network, root filesystem, mounts, capabilities, and resource limits are runtime controls. |
| Verification discipline | `tests/`, `.github/workflows/` | Tests encode important expected behavior; workflow files describe automation but are not themselves proof of a hosted run. |

## The engineering progression

1. **Observe the agent surface.** Agent instructions and tool configurations are ordinary files, but can influence what an agent attempts.
2. **Define the trust boundary.** The user supplies one scan root; the scanner treats its contents as untrusted bytes and limits discovery.
3. **Keep analysis inert.** TOML parsing produces data, text stays text, and commands remain strings. Rules inspect selected values and phrases.
4. **Minimize exposure.** Descriptor-relative reads, file-size/traversal limits, sanitized errors, and secret redaction address specific risks, each with stated limitations.
5. **Return a human-readable result.** Findings preserve evidence and context. Reviewers decide what is valid and what action to take.
6. **Add a separate runtime boundary.** Docker can restrict the auditor process, but does not change the scanner's detection coverage or turn heuristic output into a guarantee.

## Questions for a project review

- Which claim is supported by code, which by tests, and which depends on the host environment?
- What file names does discovery include, and what repository content will it miss?
- What would a malicious MCP command string do during scanning? Why?
- What does a LOW confidence label mean here, and what does it not mean?
- Which Docker controls come from the image and which must the operator request at runtime?
- Why is an empty findings list not equivalent to a safety verdict?

For the full implementation map, see [Source Code Guide](../source-code-guide.md), [Security Model](../security-model.md), and [Threat Model](../threat-model.md).
