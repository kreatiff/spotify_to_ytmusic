# Use a slim Python image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY spotify2ytmusic/ ./spotify2ytmusic/
COPY api.py test_auth.py ./

# Create an empty oauth.json if it doesn't exist (to avoid mount issues, though volume mount is preferred)
RUN touch oauth.json

# Expose the API port
EXPOSE 8080

# Run the API server
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]
