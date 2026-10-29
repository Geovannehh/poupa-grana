FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt requirements-production.txt ./
RUN pip install --no-cache-dir -r requirements-production.txt     && useradd --create-home --uid 10001 app \
    && mkdir -p /app/staticfiles && chown app:app /app/staticfiles
COPY --chown=10001:10001 . .
USER app
CMD ["python", "scripts/start_production.py"]
