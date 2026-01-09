FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for zbar
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libzbar0 \
    libzbar-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Start command
CMD sh -c "exec gunicorn --bind 0.0.0.0:${PORT:-8080} src.app:app --workers 2 --timeout 120"
