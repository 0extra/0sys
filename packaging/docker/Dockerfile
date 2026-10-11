FROM python:3.13-slim AS builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir --upgrade pip build \
    && python -m build --wheel


FROM python:3.13-slim

LABEL org.opencontainers.image.title="0sys" \
      org.opencontainers.image.description="Friendly server automation for beginner sysadmins" \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="https://github.com/0extra/0sys"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        openssh-client \
        sshpass \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir ansible-core

COPY --from=builder /build/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -f /tmp/*.whl

RUN useradd --create-home --shell /bin/bash 0sys
USER 0sys
WORKDIR /home/0sys

ENTRYPOINT ["0sys"]
CMD ["--help"]