FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if required for PDF processing or tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# For cloud platforms (Render, Railway, Fly.io)
ENV PORT=8000
EXPOSE 8000

# Start the FastMCP server with HTTP (SSE)
CMD ["python", "arxiv_mcp_server.py"]
