FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev

COPY . .

ENV PYTHONPATH=/app/src
CMD ["uv", "run", "fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]
