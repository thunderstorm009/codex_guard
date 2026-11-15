# Security Model

This document distinguishes implemented controls from claims that remain dependent on the host, platform, and detection coverage.

## Offline scan behavior

**Implemented in the scan path:** CodexGuard reads local files and evaluates them in-process. It does not start subprocesses, connect to remote servers, or start MCP services. Dependency installation, Docker image pulls/builds, and GitHub Actions are outside a CodexGuard scan and may use a network.

**Test evidence:** scanner tests replace process and socket operations with failing tripwires. That covers exercised code paths; it is not formal proof about every future change or third-party runtime behavior.

## Read-only and non-execution behavior

**Implemented:** discovered files are opened for reading. Instructions are never followed. Hooks, commands, scripts, and MCP configuration are not executed. No auto-remediation is provided.

**Observed:** tests compare scanned file contents, mode, and mtime before and after a scan; these remained unchanged. Reads can update access time on some filesystems. CodexGuard does not write to restore atime because that would modify the target.

## Root containment and symlinks

**Implemented:** callers must provide a scan root. The scanner pins the root and directories by file descriptor, opens children relative to descriptors, uses no-follow behavior where available, and does not traverse symlinked directories. The standalone TOML parser checks containment and bounds reads.

**Limit:** filesystem APIs and `O_NOFOLLOW` behavior differ by platform. The scanner fails closed when required descriptor primitives are unavailable. Race tests cover selected replacement scenarios, not every filesystem or a hostile concurrent actor.

## Resource limits

Default bounds are 1 MiB per file, 50,000 entries, 1,000 directories, depth 20, 5,000 relevant files, and 64 open directories. The result reports reached limits, and malformed or oversized files are isolated as scan errors.

The limits bound CodexGuard's traversal and reads; they do not guarantee bounded cost inside every OS API or parser. Fixed defaults may need review for unusually large repositories.

## Rules and redaction

Seven rules cover selected sandbox and approval values, suspicious MCP command forms, `CODEX_HOME` assignments in environment examples, common credentials, hook presence, and selected instruction phrases. Findings are heuristic prompts and may have false positives or false negatives. The confidence field describes pattern-match confidence, not exploitability.

Redaction handles selected credential assignments and token forms, bearer values, URL credentials, and supported private-key blocks. It is not complete; unknown encodings, split values, new providers, and custom credential formats can evade it. Review suspected exposures securely and rotate credentials confirmed to be real.

## Report output

Output is optional and must be explicitly requested outside the resolved scan root. The writer refuses existing files, uses exclusive creation, rejects symlink paths where supported, and cleans partial output after a failed write.

A same-user process may race directory entries. In particular, a hostile process that can write both the report directory and scan root could hard-link a newly created report into the scan tree while it is being written. This residual race is documented; exclusive creation prevents overwriting a pre-existing inode but does not make publication atomic on all supported filesystems. Use a private, controlled report directory.

## Docker

The image configures UID/GID 10001. Local Docker Desktop validation recorded a read-only root and scan mount, separate writable report mount, disabled networking, dropped capabilities, no-new-privileges, and memory/CPU/PID limits. The tests apply only to the recorded macOS Docker Desktop environment, not every daemon or hosted Linux runner. See [Docker Guide](docker-guide.md).

## Python and test-tool security

Package metadata declares Python `>=3.9` for compatibility. Python 3.9 and 3.10 are end-of-life and are not security-supported runtimes. The development lock pins pytest 9.0.3 for Python 3.11+; the GitHub-reviewed [CVE-2025-71176 / GHSA-6w46-j5rx-g56g](https://github.com/advisories/GHSA-6w46-j5rx-g56g) affects pytest versions below 9.0.3, and pytest 9.0.3 requires Python >=3.10.

The current local Python 3.9.6 test run used pytest 8.4.2 and passed 63 tests, but that pytest version is affected. Treat the run only as historical/functional compatibility evidence, not as a secure development environment or supported-runtime CI result. Use the locked Python 3.11+ toolchain for release testing.

## Current release boundary

Local tests, static checks, Docker tests, and Git history scans are evidence only for the commands and files actually exercised. At the pre-publication check on 2026-11-15, GitHub showed the intended repository as empty with zero registered workflows and zero workflow runs. Remote CI must be checked after publication. The existing local root commit omits package metadata and the vulnerable fixture referenced by its workflows; the current release payload prepares these files for a follow-up commit. See [Release Readiness](release-readiness.md) for the verified pre-publication evidence.
