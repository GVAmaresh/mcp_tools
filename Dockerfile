# Stage 1: Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install poetry for dependency management
# Using Poetry or another tool is more robust than pip for managing dependencies
# For simplicity here, we'll stick to pip
ENV PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
CMD ["uvicorn", "mcp_server:app", "--host", "0.0.0.0", "--port", "8000"]