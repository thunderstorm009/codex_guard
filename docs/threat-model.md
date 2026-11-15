# Threat Model

## Scope and security objective

CodexGuard audits a user-selected directory for a bounded set of Codex configuration and project files. The primary goal is to inspect untrusted content as inert data without executing it, changing it, or making network requests.

## Assets

- Contents and metadata of the selected project.
- Credentials that may be present in configuration or environment examples.
- Host files and process environment outside the selected project.
- Integrity of generated reports and pre-existing user files.
- Availability of the scanner process under hostile file trees or inputs.

## Trust boundaries and actors

- The scan root is user-selected; files and directory entries inside it are untrusted.
- A malicious repository contributor may provide crafted instructions, TOML, environment examples, symlinks, special files, huge directory trees, or rapidly changing paths.
- A local concurrent process may modify path entries while scanning or report generation is in progress.
- The CLI user controls the scan root, report path, and severity/format arguments.
- The operating system and Python runtime provide filesystem and parser primitives; their behavior varies across platforms.

## Attack surfaces and scenarios

1. A crafted hook or MCP command attempts execution during inspection.
2. A symlink or traversal path directs reads outside the selected root.
3. Rapid replacement between validation and open changes which object is inspected.
4. A malicious input exhausts memory, descriptors, CPU, or traversal time.
5. Secret-like text leaks through findings, parser errors, logs, or reports.
6. A report path aliases an existing scan file through a symlink or hard link and overwrites it.
7. Malformed TOML or text causes a whole-scan failure or leaks parser internals.
8. A plausible but benign configuration triggers an inaccurate finding.

## Controls in the implementation

- Scanner treats configuration and instructions as bytes/text; it does not call a shell, subprocess, network library, hook, or MCP server.
- Bounded entry, directory, depth, relevant-file, open-descriptor, and byte limits constrain resource use. Reached limits are reported.
- Discovery uses pinned directory descriptors and no-follow child opens on supported platforms; symlinked directory entries are skipped.
- TOML parse errors and filesystem errors use sanitized messages. Secret redaction is applied to evidence, result dictionaries, report paths, and errors.
- Report output is outside the resolved scan root, rejects existing paths and symlinks, uses exclusive creation, and cleans up partial writes.
- Tests use temporary directories and synthetic credentials to exercise traversal, symlink, output alias, error, and read-only behavior.
- Docker is configured for a non-root user; the documented invocation adds read-only root and scan mounts, disabled networking, dropped capabilities, no-new-privileges, and resource limits.

## Residual risks

- File-system race behavior and descriptor APIs differ by platform; no complete race guarantee is claimed.
- Secret matching is heuristic and may miss novel, encoded, split, or application-specific credentials.
- Rules can have false positives and false negatives; detection does not prove malicious intent or runtime exploitability.
- Only a limited set of file names and formats is scanned, and effective settings may be inherited or supplied elsewhere.
- An attacker with the same OS account can race report or scan operations within platform filesystem semantics.
- Docker Desktop on macOS relies on a managed Linux VM and shared-folder implementation; enforcement must be checked in the actual deployment environment.
- CI workflow files are defined but are not proof of a passing GitHub Actions run until connected to a repository and executed.

## Out of scope

CodexGuard does not validate Codex runtime behavior, inspect all host state, remediate files, verify command provenance, or provide complete security coverage or certification.
