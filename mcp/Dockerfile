FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-cache

ENV PATH="/app/.venv/bin:${PATH}"

COPY . .

EXPOSE 9090

CMD ["python", "src/mcp/server.py", "--port", "9090", "--host", "0.0.0.0", "--transport", "streamable-http"]