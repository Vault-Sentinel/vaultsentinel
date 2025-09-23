FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Node.js
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build the React frontend
WORKDIR /app/packages/ui
RUN npm install
RUN npm run build

# Return to app directory
WORKDIR /app

# Create data directory
RUN mkdir -p /app/data

# Create non-root user
RUN useradd -m -u 1000 vaultsentinel && \
    chown -R vaultsentinel:vaultsentinel /app
USER vaultsentinel

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/healthz || exit 1

# Run the application
CMD ["python", "main.py"]
