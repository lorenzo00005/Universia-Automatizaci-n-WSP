# El worker comparte código con la API (modelos y dominios), así que se construye
# desde apps/api y sólo cambia el comando de arranque.
FROM python:3.12-slim
RUN pip install --no-cache-dir uv==0.9.5
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1 PATH="/app/.venv/bin:$PATH"
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app
CMD ["arq", "app.worker.main.WorkerSettings"]
