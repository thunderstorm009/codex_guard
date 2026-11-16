# Threat Model

## Scope and objective

CodexGuard audits a bounded set of Codex configuration and project files under a user-selected directory. Its objective is to inspect untrusted content as inert data, emit useful heuristic warnings with redacted evidence, and avoid intentional writes to the selected tree or execution of discovered behavior.

CodexGuard does not prove that a project is safe, evaluate the complete effective Codex runtime policy, or provide security certification.

## Assets

- Contents and metadata of the selected project.
- Credentials that may be present in configuration and example files.
- Host files and process state outside the selected root.
- Integrity of reports and pre-existing user data.
- Availability of the scanner under hostile trees or malformed files.

## Trust boundaries and assumptions

- The selected root is supplied by the CLI user. Files and entries below it are untrusted.
- A repository contributor may provide malicious TOML, instructions, environment examples, symlinks, special files, oversized inputs, or rapidly changing paths.
- Another process running with the user's permissions may race scan or report operations.
- The OS, Python runtime, parser, and filesystem enforce descriptor, symlink, and permission semantics; those vary by platform.
- The caller is responsible for choosing a trusted report destination outside the scan root and protecting report contents.

## Attack surface and scenarios

1. A hook or MCP command string attempts to cause execution during inspection.
2. A traversal path or symlink attempts to direct reads outside the selected root.
3. A path is replaced between discovery and open.
4. A huge or deep tree, oversized file, or malformed TOML exhausts resources.
5. A secret leaks through evidence, paths, parser exceptions, logs, or reports.
6. A report destination aliases a scanned file through an existing symlink or hard link.
7. A plausible but benign setting or instruction triggers a false positive.
8. An obfuscated secret or unsafe instruction evades pattern-based detection.

## Implemented controls and evidence

- Input commands, hooks, scripts, and MCP definitions are treated as data. Tests install subprocess and socket tripwires and verify a marker command is not run.
- Discovery is restricted to `AGENTS.md`, `.codex/config.toml`, `.env.example`, and `.env.*.example` beneath the explicit root.
- Descriptor-relative traversal, no-follow flags, and pinned directory descriptors prevent tested symlink traversal and path swaps on the exercised macOS platform.
- Defaults bound each file to 1 MiB; discovery to 50,000 entries, 1,000 directories, depth 20, 5,000 relevant files, and 64 open directory descriptors. Reached limits are reported.
- TOML parse and filesystem errors are sanitized. Findings and report fields pass through secret redaction.
- Report output must be requested, outside the scan root, and not already present. Exclusive creation refuses existing destinations, including pre-existing hard links. Symlinked output paths are rejected where supported, and partial files are cleaned after simulated write failure.
- Tests compared content, mode, and mtime before and after scanning. The exercised file contents and these metadata fields remained unchanged. Ordinary reads may update atime on other filesystems.
- Docker was built and exercised locally as a non-root user with a read-only root and scan mount, separate writable report mount, network disabled, capabilities dropped, no-new-privileges, and memory/CPU/PID limits.

See [Experiment Results](experiment-results.md) and [Docker Guide](docker-guide.md) for the evidence scope and environment.

## Heuristics and false positives / negatives

Rules match selected explicit settings and text patterns. A benign shell wrapper can match CG-003; a benign hook is only a low-severity manual-review prompt; instruction wording can be contextually harmless. Conversely, obfuscation, alternative config locations, inherited settings, split credentials, and unsupported secret formats can evade detection. A finding is not proof of compromise, intent, or exploitability. Review effective configuration and context manually.

## Residual risks and limitations

- Descriptor and `O_NOFOLLOW` support is platform-specific. The scanner fails closed when required traversal primitives are missing, but Windows and other filesystems have not been independently verified.
- Deterministic race tests are not exhaustive stress tests. Concurrent same-user modification cannot be completely excluded.
- Exclusive report creation prevents replacing an existing inode. A hostile same-user process may still race a newly created report into the scan tree as a hard link while it is being written; this is a known portability limitation.
- Parsing a near-limit file can use more memory than its byte size. Operating-system, Python, and parser resource use is not fully bounded by CodexGuard.
- Atime updates may happen as a filesystem consequence of reading.
- Redaction does not cover all secrets. A clean Gitleaks or CodexGuard scan does not establish absence of credentials.
- Docker restrictions depend on host kernel, daemon, and (on macOS) Docker Desktop's managed Linux VM and shared-folder behavior.
- Historical note: on 2026-11-15, before publication, GitHub was observed empty with no registered workflows or runs. That point-in-time observation and the missing-file assessment are not statements about the current published repository. Local workflow files still are not proof of a hosted CI result.

## Out of scope

CodexGuard does not inspect all host state, establish command provenance, enforce Codex policy, validate live runtime behavior, remediate files, or promise complete detection.
