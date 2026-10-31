FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 ED_DATABASE=/app/data/evidencedesk.sqlite3
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir . && useradd --uid 10001 --create-home appuser && mkdir -p data && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=2)"
CMD ["python", "-m", "evidencedesk.cli", "serve", "--host", "0.0.0.0"]
