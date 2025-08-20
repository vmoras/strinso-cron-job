# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY main.py .

USER appuser

CMD ["python", "main.py"]
