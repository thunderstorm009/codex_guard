# CodexGuard Phase 3 Security Audit

## Scope

This review examined CodexGuard's filesystem parsing and discovery, report output, secret redaction, rules CG-001 through CG-007, resource limits, CLI output paths, and read-only / non-execution behavior. Probes used temporary directories and synthetic credentials only. No discovered command, hook, script, or MCP server was run. CodexGuard itself made no network request; the reviewer consulted public upstream Codex source to avoid unsupported claims about approval behavior.

The audit is a code review and regression test exercise, not a certification or proof of complete protection.

## Methodology

- Inspected `config_parser.py`, `scanner.py`, `reporter.py`, `rules.py`, `cli.py`, rule data, fixtures, tests, and documentation.
- Exercised report creation against existing paths, symlinks, parent symlinks, hard links, and simulated partial write failures.
- Simulated a directory and file being replaced by external symlinks at the point of opening.
- Probed secret redaction with quoted and escaped assignments, bearer values, URL user information, command arguments, multiple values, private-key material, Stripe-style keys, JWT-like strings, and secret-like paths.
- Created broad and deeply nested temporary directory trees and exercised entry, directory, depth, open-descriptor, relevant-file, and byte limits.
- Compared scanned file content, mode, and modification time before and after a scan. The current test filesystem did not change atime in a separate probe.
- Ran the Python 3.9 pytest suite and both supplied fixture scans.

## Findings

### Confirmed vulnerability — external symlink race during directory traversal — fixed

- **Severity:** High
- **Affected file:** `codexguard/scanner.py`
- **Evidence:** Path-based traversal can check a directory entry and later reopen it by pathname. A directory can be replaced with a symlink between those operations; `followlinks=False` alone does not pin the checked directory object.
- **Reproduction:** Create `scan/nested/` and an outside directory containing a suspicious `AGENTS.md`. During the child-directory open, rename `scan/nested` and replace its old path with a symlink to the outside directory. The prior pathname-based approach could enumerate outside content.
- **Fix:** The scanner now pins the selected root and child directories with directory file descriptors, opens children relative to their parent descriptors with no-follow flags, and reads relevant files from the same pinned parent descriptor. It fails closed when required descriptor primitives are unavailable. Regression tests swap both directories and files to external symlinks at open time.

### Confirmed vulnerability — escaped quoted credential could leak in evidence — fixed

- **Severity:** High
- **Affected file:** `codexguard/rules.py`
- **Evidence:** The previous quoted assignment pattern stopped at an escaped quote. For example, `API_KEY="prefix\\"escaped-secret-suffix"` was partially redacted but left `escaped-secret-suffix` in the output.
- **Fix:** Quoted assignment patterns now consume escaped characters within the quoted value. Regression coverage confirms the suffix does not appear in redacted output.

### Confirmed detection gap — common token formats were not recognized — fixed

- **Severity:** Medium
- **Affected file:** `codexguard/rules.py`
- **Evidence:** Probe values shaped like `sk_live_...` and three-part JWT strings were unchanged by the previous redactor and did not match its credential patterns.
- **Fix:** Added patterns for Stripe-style keys and JWT-shaped values, plus tests. Detection remains heuristic and does not cover arbitrary encodings or every provider format.

### Informational — report output protections verified

- **Severity:** Informational
- **Affected file:** `codexguard/reporter.py`
- **Evidence:** Existing paths fail exclusive creation; a hard link to a scanned file is an existing path and is rejected; final symlinks and parent symlinks are rejected; parent directories are traversed by descriptor with no-follow flags where available; a simulated partial write removes the created report.
- **Reproduction:** These cases are covered by `tests/test_reporter.py` (`existing_file`, `symlink_destination`, `symlink_parent`, `hard_link`, and `failed_write` tests).
- **Remaining caveat:** A same-privilege concurrent process that can mutate both the output directory and scan root may race report publication or create a new hard link to a report while it is being written. Existing scanned inodes are not overwritten by the normal exclusive-create path. A fully hostile same-user concurrent filesystem actor is outside this portable implementation's guarantees.

### Potential weakness — concurrent report hard-link alias — not fully preventable portably

- **Severity:** Low, conditional on a concurrent process with the same user's filesystem permissions
- **Affected file:** `codexguard/reporter.py`
- **Evidence:** Exclusive creation prevents overwriting a pre-existing hard link, but the destination inode exists while `write_report` writes its contents. A same-privilege process could link that newly created inode into the scan root before the write completes, making the report visible under a scanned-tree path.
- **Reproduction:** Pause a report writer after exclusive creation and before its first write. From another same-user process, hard-link the new destination into the scan root, then allow the writer to continue. The alias receives the report content. This does not overwrite a pre-existing scanned inode, but breaks output/input separation under the stated race.
- **Recommendation:** If the threat model includes a hostile concurrent same-user process, publish a fully written private temporary file atomically and use platform-specific facilities such as anonymous temporary files where available. Keep the current exclusive-create behavior as the portable baseline.

### Informational — rule wording and context reviewed

- **Severity:** Informational
- **Affected files:** `codexguard/rules.py`, `rules/security_rules.json`, fixtures, and rule tests.
- **Evidence:** CG-004 now requires an actual `CODEX_HOME` assignment in an environment example; a TOML `codex_home` field alone does not trigger it. CG-002 reports `approval_policy = "never"` with sandbox context and lower severity for restricted/unknown modes; effective policy may come from other configuration layers. Current Codex source describes `never` as changing prompt behavior while sandbox policy still affects command decisions. [Codex execution policy](https://github.com/openai/codex/blob/main/codex-rs/core/src/exec_policy.rs)
- **Evidence:** CG-006 is a LOW-severity manual-review reminder. It says hook presence is not evidence of unsafe behavior; no hook command is executed.
- **Remaining caveat:** Rules are intentionally narrow heuristics. CG-003 can miss obfuscated commands and can flag benign shell wrappers; CG-007 can miss or overmatch natural-language instructions; CG-001 only recognizes selected explicit values.

### Informational — resource limits and read-only behavior exercised

- **Severity:** Informational
- **Affected files:** `codexguard/scanner.py`, `codexguard/config_parser.py`, tests, and docs.
- **Evidence:** Discovery tracks total entries, directories, depth, relevant files, and open directory descriptors; reads are byte-bounded; oversized and malformed inputs become per-file errors. Limits are returned in summaries. Symlink directories are not followed. Tests verify scanned contents, mode, and mtime remain unchanged and that no process or network call is made.
- **Read-only observation:** On the current macOS test filesystem, a probe found no atime change after scanning. Ordinary reads may update access times on other filesystems or mount configurations; CodexGuard does not attempt to restore metadata because doing so would itself write to scanned files.

## Explicitly unverified areas

- Windows and other platforms lacking descriptor-based `scandir`, `O_NOFOLLOW`, or directory-relative `open` were not exercised; scanner discovery fails closed when required primitives are absent.
- The scan-root identity test and race probes are deterministic simulations, not exhaustive concurrent stress testing across filesystems.
- Behavior on network filesystems, unusual mount options, immutable files, ACL-denied trees, and filesystems with atypical hard-link semantics was not independently tested.
- Resource tests use bounded temporary trees, not multi-million-entry stress workloads. Defaults cap work, but parsing a near-limit 1 MiB structured document can still consume more memory than its source size.
- Redaction does not recognize all credentials, encodings, custom token formats, split secrets, or every private-key syntax. A clean scan does not establish that a tree is safe.
- Docker was not built or run as part of this audit.

## Recommendations

- Keep the descriptor-based traversal and exclusive report creation regression tests mandatory.
- Consider a stricter operating-system-specific report publication mechanism if the threat model includes a concurrent process running under the same user identity.
- Expand credential patterns only with synthetic tests and explicit false-positive review.
- Review findings manually and do not interpret rule matches as proof of compromise.

## Later evidence and status note

This file is the Phase 3 point-in-time audit record; its scope and results above were not retroactively changed. Later local evidence records 63 tests passing on the current Python 3.9.6 environment, but its pytest 8.4.2 is affected by CVE-2025-71176 and is not safe release-toolchain evidence. Prior Phase 7.1 records a patched pytest 9.0.3 test matrix on Python 3.11–3.14. Later Docker verification is recorded in [docker-guide.md](docker-guide.md).

At the pre-publication check on 2026-11-15, GitHub reported the intended repository empty with no registered workflows or runs. The existing local root commit was incomplete for installation and CI because it omits package metadata and the vulnerable fixture referenced by its workflows. A later release payload is being prepared to add those files. See [project-status.md](project-status.md) and [release-readiness.md](release-readiness.md) for the publication evidence and current handover.
