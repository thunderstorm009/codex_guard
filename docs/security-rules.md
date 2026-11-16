# Security Rules

CodexGuard ships seven heuristic rules. The implementation is in [`codexguard/rules.py`](../codexguard/rules.py), with rule metadata in [`rules/security_rules.json`](../rules/security_rules.json). The packaged catalog at [`codexguard/security_rules.json`](../codexguard/security_rules.json) is expected to match.

| ID | Rule | Default severity | Input / behavior |
|---|---|---:|---|
| CG-001 | Dangerous Sandbox Configuration | CRITICAL | Parsed TOML values for `sandbox_mode`, `sandbox`, or a `mode` field under a sandbox path; recognizes `danger-full-access`, `unsafe`, `disabled`, `none`, and `false`. |
| CG-002 | No-Prompt Approval Policy | LOW; MEDIUM conditionally | Top-level `approval_policy = "never"`; raises to MEDIUM only when top-level `sandbox_mode` is `danger-full-access`. |
| CG-003 | Suspicious MCP Configuration | HIGH | Top-level `mcp_servers` commands and arguments containing `sh|bash|zsh -c`, `curl`/`wget` piped to a shell, or `python -c` / `python3 -c`. |
| CG-004 | CODEX_HOME Redirection | MEDIUM | Assignment-like `CODEX_HOME=...` lines (optional `export`) in discovered environment example files. |
| CG-005 | Potential Secret Exposure | HIGH | Selected credential patterns in TOML values or text lines, with evidence redacted before reporting. |
| CG-006 | Hook Requires Manual Review | LOW | A top-level `hooks` value that is non-empty and not `false`; presence alone is not characterized as unsafe. |
| CG-007 | Suspicious Project Instructions | MEDIUM | Selected instruction override, secret/token/credential sending, download-to-shell, or `exfiltrat` phrases in `AGENTS.md`. |

## Rule details

### CG-001 — Dangerous Sandbox Configuration

Checks selected explicit values in parsed Codex TOML. This does not model every valid setting or layered effective configuration. Review the runtime configuration source and intended scope.

### CG-002 — No-Prompt Approval Policy

Checks only the top-level approval value in the parsed config. It does not infer behavior from all configuration layers. `never` alone is LOW; the exact same-file `danger-full-access` sandbox value raises this finding to MEDIUM. This rule does not state that approval policy overrides sandbox restrictions.

### CG-003 — Suspicious MCP Configuration

Joins each configured server's `command` and `args` and looks for a narrow set of shell and inline execution patterns. Shell use may be legitimate, and obfuscation or other invocation forms may evade the rule. CodexGuard never launches an MCP process.

### CG-004 — CODEX_HOME Redirection

Checks assignment-shaped lines in `.env.example` and `.env.*.example` files. It does not detect arbitrary environment-setting mechanisms, and an example assignment is not proof that the variable is set at runtime.

### CG-005 — Potential Secret Exposure

Checks selected assignment names, command-line flags, bearer values, URL credentials, private-key blocks, and common provider token shapes. Coverage is incomplete. Findings and serialized paths/errors pass through redaction, but unknown, split, or custom secrets may not be recognized. Confirm a match safely; rotate a credential confirmed to be real.

### CG-006 — Hook Requires Manual Review

Any non-empty top-level `hooks` setting in the scanned config produces a LOW reminder. The rule does not inspect whether a hook is safe, trusted, or appropriate. Read the hook source and understand its triggers and effects without asking CodexGuard to execute it.

### CG-007 — Suspicious Project Instructions

Matches a short phrase set in discovered `AGENTS.md` files. Natural language requires context: benign documentation can match, while differently worded instructions can evade detection. Review the surrounding project guidance and its provenance.

## Interpreting severity and confidence

Severity and confidence are rule metadata. Confidence describes the pattern match, not likelihood of exploitation. Findings are evidence for review, not vulnerability confirmations. A clean report means only that these rules did not match the files that were discovered and read successfully.

The catalog has two copies because one is the source-facing rule list and one is bundled for package use. [`tests/test_packaging.py`](../tests/test_packaging.py) contains a consistency check; it has not been run during this documentation update.
