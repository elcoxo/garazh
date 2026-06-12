FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen

COPY . .

CMD ["uv", "run", "fastapi", "dev", "main.py", "--host", "0.0.0.0"]
