# Docker Guide

## Image design

`docker/Dockerfile` uses the official Python 3.12 slim image pinned by digest (`python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`), installs the local package with the pinned `flit_core==4.2.0` build backend, and sets the runtime identity to UID/GID 10001. Flit Core was selected because it supports Python 3.9, unlike the previously considered setuptools release. It has no Codex CLI, MCP process, or embedded secret. The local image reports Python 3.12.16; the application has no third-party runtime dependency on Python 3.12 because TOML parsing uses the standard library.

## Build and inspect

From the repository root:

```sh
docker build -t codexguard:latest -f docker/Dockerfile .
docker image inspect codexguard:latest --format '{{.Config.User}}'
```

Expected configured user is `10001:10001`.

## Restricted run

Prepare a separate report directory that is writable by UID 10001 on the Docker host. Keep the target read-only:

```sh
docker run --rm \
  --network none \
  --read-only \
  --cap-drop ALL \
  --security-opt no-new-privileges \
  --memory 256m \
  --cpus 1 \
  --pids-limit 64 \
  --mount type=bind,src="$(pwd)/fixtures/vulnerable",dst=/scan,readonly \
  --mount type=bind,src="$(pwd)/reports",dst=/reports \
  codexguard:latest scan /scan --format json --output /reports/audit.json
```

The vulnerable fixture is expected to produce findings and return status 1. Docker does not imply complete isolation; host kernel, daemon, mount implementation, and configuration remain relevant.

## Validation in this workspace

Recorded environment: macOS, Docker CLI and daemon 29.6.2. The first attempt with `python:3.13.18-slim-bookworm` could not resolve Docker Hub metadata before the build deadline. A local official Python 3.12.16 slim image was available, so the Dockerfile was pinned to its repo digest and the build then succeeded.

- `docker build -t codexguard:latest -f docker/Dockerfile .`: **passed**.
- `docker image inspect codexguard:latest --format 'User={{.Config.User}} Entrypoint={{json .Config.Entrypoint}} Workdir={{.Config.WorkingDir}}'`: **passed**, output `User=10001:10001 Entrypoint=["codexguard"] Workdir=/opt/codexguard`.
- Restricted runtime profile: **passed**. `docker inspect` showed network `none`, read-only root enabled, memory `268435456`, NanoCPUs `1000000000`, PID limit `64`, dropped capabilities `["ALL"]`, and security option `["no-new-privileges"]`.
- In-container checks: **passed**. Effective UID was 10001, effective capabilities were zero, `NoNewPrivs` was 1, writes to the root filesystem and `/scan` failed, and a write to `/reports` succeeded.
- Vulnerable fixture scan in the restricted container: **passed** with 3 files scanned, 8 findings, 0 errors, expected exit 1; JSON was created on the separate report mount and parsed on the host.
- Hardened fixture scan in the restricted container: **passed**, exit 0.
- Release-readiness recheck on 2026-11-15 after updating the build backend pin: `docker build -t codexguard:release-check -f docker/Dockerfile .` and image inspection **passed**. The updated image again ran the vulnerable fixture with 8 findings / exit 1 and the hardened fixture with 0 findings / exit 0 under the restricted runtime flags above. UID 10001, zero effective capabilities, `NoNewPrivs=1`, and denied writes to the root filesystem and scan mount were rechecked.

The validation used a temporary report directory with permissive mode so UID 10001 could write through the macOS bind mount. Set a private report directory and suitable host permissions for normal use. Docker Desktop on macOS runs containers in a managed Linux VM; shared-folder permissions and resource enforcement still depend on Docker Desktop and host configuration. These results verify the tested controls in this local setup, not complete container isolation.

## Source-tree and release note

The build/runtime evidence above was obtained from the complete local working tree. The existing root Git commit does not include `pyproject.toml` or `fixtures/vulnerable/`; the follow-up release payload prepared in this workspace includes them. Before publication, GitHub was observed empty with no workflow runs on 2026-11-15. Verify the source tree and Actions status after publishing.
