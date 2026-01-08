# Use Python 3.11 as base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV and wget for downloading models
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libgtk-3-0 \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY opencv_mcp_server/ ./opencv_mcp_server/
COPY OPENCV_DNN_MODELS_DIR/ ./OPENCV_DNN_MODELS_DIR/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Download YOLOv3 model files (weights, config, and class names)
# Note: We copy local files first, then download weights if not present
RUN mkdir -p /app/OPENCV_DNN_MODELS_DIR && \
    cd /app/OPENCV_DNN_MODELS_DIR && \
    if [ ! -f yolov3.weights ]; then \
        echo "Downloading YOLOv3 weights (237MB)..." && \
        wget -q --progress=bar:force:noscroll https://pjreddie.com/media/files/yolov3.weights && \
        echo "Downloaded yolov3.weights"; \
    else \
        echo "yolov3.weights already exists, skipping download"; \
    fi && \
    if [ ! -f yolov3.cfg ]; then \
        echo "Downloading yolov3.cfg..." && \
        wget -q https://raw.githubusercontent.com/pjreddie/darknet/master/cfg/yolov3.cfg && \
        echo "Downloaded yolov3.cfg"; \
    else \
        echo "yolov3.cfg already exists, skipping download"; \
    fi && \
    if [ ! -f coco.names ]; then \
        echo "Downloading coco.names..." && \
        wget -q https://raw.githubusercontent.com/pjreddie/darknet/master/data/coco.names && \
        echo "Downloaded coco.names"; \
    else \
        echo "coco.names already exists, skipping download"; \
    fi && \
    echo "YOLO model files:" && \
    ls -lh yolov3.* coco.names 2>/dev/null || echo "Some files may be missing"

# Create directories for input/output files
RUN mkdir -p /data/input /data/output

# Set environment variables
ENV MCP_TRANSPORT=stdio
ENV OPENCV_DNN_MODELS_DIR=/app/OPENCV_DNN_MODELS_DIR
ENV PYTHONUNBUFFERED=1

# Default command - run the MCP server
CMD ["python", "-m", "opencv_mcp_server.main"]

