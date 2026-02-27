# Use Ubuntu 24.04 which has glibc 2.39 (required for ferreus_rbf manylinux_2_39 wheel)
FROM ubuntu:24.04

# Install Python 3.12 and pip
RUN apt-get update && apt-get install -y \
    python3.12 \
    python3-pip \
    python3.12-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment (required on Ubuntu 24.04 due to PEP 668)
RUN python3.12 -m venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Railway will set $PORT)
ENV PORT=8080
EXPOSE $PORT

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port $PORT
