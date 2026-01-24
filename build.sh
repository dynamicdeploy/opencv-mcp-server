#!/bin/bash
# Script to build OpenCV MCP Server Docker image

set -e  # Exit on error

# Configuration
IMAGE_NAME="opencv-mcp-server"
VERSION=$(grep -E '^version = ' pyproject.toml | sed -E 's/version = "([^"]+)"/\1/')

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "OpenCV MCP Server - Docker Image Builder"
echo "=========================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo -e "${RED}ERROR: Dockerfile not found in current directory${NC}"
    exit 1
fi

echo -e "${GREEN}Image name: ${IMAGE_NAME}:latest${NC}"
echo -e "${GREEN}Version: ${VERSION}${NC}"
echo ""

# Build the image
echo -e "${GREEN}Building Docker image...${NC}"
docker build -t ${IMAGE_NAME}:latest .

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Docker build failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Build successful!${NC}"
echo ""
echo "Built image: ${IMAGE_NAME}:latest"
echo ""
echo "To test the image:"
echo "  docker run -i --rm ${IMAGE_NAME}:latest"
echo ""
echo "To tag for Docker Hub:"
echo "  docker tag ${IMAGE_NAME}:latest <username>/${IMAGE_NAME}:latest"
echo ""
echo "=========================================="
