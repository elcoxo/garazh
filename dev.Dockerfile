FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen

COPY . .

ENV PYTHONPATH=/app/src
CMD ["uv", "run", "fastapi", "dev", "--host", "0.0.0.0"]
