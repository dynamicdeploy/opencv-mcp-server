# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY opencv_mcp_server/ ./opencv_mcp_server/
COPY OPENCV_DNN_MODELS_DIR/ ./OPENCV_DNN_MODELS_DIR/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create directories for input/output files
RUN mkdir -p /data/input /data/output

# Set environment variables
ENV MCP_TRANSPORT=stdio
ENV OPENCV_DNN_MODELS_DIR=/app/OPENCV_DNN_MODELS_DIR
ENV PYTHONUNBUFFERED=1

# Default command - run the MCP server
CMD ["python", "-m", "opencv_mcp_server.main"]

