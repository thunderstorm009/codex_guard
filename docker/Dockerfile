FROM python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /opt/codexguard
COPY pyproject.toml README.md ./
COPY codexguard ./codexguard
RUN python -m pip install --no-cache-dir . \
    && useradd --system --uid 10001 --create-home --home-dir /home/codexguard codexguard

USER 10001:10001
ENTRYPOINT ["codexguard"]
CMD ["--help"]
