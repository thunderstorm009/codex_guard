# 03 — Basic Docker Concepts

## Purpose

Use your assigned Poridhi Docker fundamentals lab to connect images, containers, identities, filesystem mounts, and runtime options to CodexGuard's deployment. The image packages the auditor; the scan target and report destination are separate mounts.

## Learning outcomes

- Explain the difference between an image's build-time configuration and a container's runtime restrictions.
- Trace the configured user, entrypoint, working directory, and copied files in the Dockerfile.
- Explain why read-only input and a separate output mount are useful for an audit tool.

## Guided activity

1. Complete the Poridhi Docker lab and record its actual name/version in your notes.
2. Read [`docker/Dockerfile`](../../../docker/Dockerfile) and [`docs/docker-guide.md`](../../docker-guide.md). Identify the Python base, work directory, installed package, UID/GID, and entrypoint.
3. Draw the run's three filesystem areas: image/root filesystem, read-only `/scan`, and writable `/reports`.
4. Review the example invocation in the Docker Guide. Mark which restrictions are in the image and which are flags on `docker run`.
5. If you choose to build and run this repository's image, do so only after reviewing its Dockerfile and using the documented sample fixtures. A Docker build executes instructions from the Dockerfile; do not build untrusted images.

## Check your understanding

- Does `USER 10001:10001` make the scan mount read-only?
- What happens to report output if `/reports` is absent or not writable?
- Does packaging CodexGuard in a container prove that its rules are complete?

## Expected artifact

A labeled container diagram that distinguishes image contents, container process settings, input mount, output mount, and host/daemon boundary.
