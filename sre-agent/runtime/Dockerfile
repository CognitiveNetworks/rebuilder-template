FROM python:3.12-slim AS base

WORKDIR /app

# Install dependencies (build context is sre-agent/, not runtime/)
COPY runtime/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY runtime/*.py .

# Copy WINDSURF_SRE.md into the container
COPY WINDSURF_SRE.md /app/WINDSURF_SRE.md

# Run as non-root
RUN useradd --create-home appuser

# Create incidents directory (must be owned by appuser)
RUN mkdir -p /app/incidents && chown appuser:appuser /app/incidents

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
