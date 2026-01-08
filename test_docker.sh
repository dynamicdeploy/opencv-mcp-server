#!/bin/bash
# Test script for running tests in Docker container

echo "=========================================="
echo "Testing OpenCV MCP Server in Docker"
echo "=========================================="

# Build the image if not exists
if ! docker image inspect opencv-mcp-server:latest > /dev/null 2>&1; then
    echo "Building Docker image..."
    docker build -t opencv-mcp-server:latest .
fi

# Copy test files to a temp directory
TEST_DIR=$(mktemp -d)
cp test_url_processing.py "$TEST_DIR/"
cp image_urls.txt "$TEST_DIR/"

echo "Running tests in Docker container..."
docker run --rm \
    -v "$TEST_DIR:/tests" \
    opencv-mcp-server:latest \
    python /tests/test_url_processing.py

# Cleanup
rm -rf "$TEST_DIR"

echo "=========================================="
echo "Docker tests completed"
echo "=========================================="


