# Enhanced Dockerfile with better Chrome configuration
FROM python:3.11-slim

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl unzip gnupg wget xvfb \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libdrm2 libxcomposite1 libxdamage1 libxrandr2 libgbm1 libxss1 libgconf-2-4 \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chrome
ENV PYTHONUNBUFFERED=1 \
    CHROME_BIN=/usr/bin/chromium \
    CHROMEDRIVER_PATH=/usr/bin/chromedriver \
    DISPLAY=:99 \
    CHROME_NO_SANDBOX=true \
    CHROME_DISABLE_DEV_SHM=true

# Set work directory
WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ .
COPY config/ ./config/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/output && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "app.py"]
