# 04 — Container Hardening Lab

## Purpose

Build on Docker fundamentals and relate least privilege and resource controls to the restricted invocation documented for CodexGuard. The Dockerfile configures a non-root identity; several further restrictions are supplied by the operator at container start.

## Learning outcomes

- Identify network, filesystem, capability, privilege-escalation, and resource controls in the documented command.
- Distinguish an implementation setting from historical evidence that a profile was tested.
- State what container restrictions do not guarantee.

## Guided activity

1. Complete the relevant Poridhi container-security lab and record its title and environment.
2. In [`docs/docker-guide.md`](../../docker-guide.md), annotate `--network none`, `--read-only`, `--cap-drop ALL`, `--security-opt no-new-privileges`, `--memory`, `--cpus`, and `--pids-limit`.
3. Explain why the scan mount is read-only while the report mount must remain writable.
4. Read the Docker validation section in the guide. Separate observed local Docker Desktop results from general guarantees.
5. Review [`docs/security-model.md`](../../security-model.md) and list two remaining risks tied to host kernel, filesystem, daemon, or same-user access.

## Check your understanding

- Which restrictions can be seen in the Dockerfile alone?
- Why is `--network none` useful even though the scan path is designed to be offline?
- What does a successful local restricted run establish, and what does it not establish?

## Expected artifact

A two-column control sheet: **control and configuration location** / **residual limit**. Do not describe containerization as a complete security boundary.
