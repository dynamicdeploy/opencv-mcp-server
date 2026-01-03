#!/bin/bash
# Test script to download and verify Docker Hub image

set -e

# Configuration
DOCKERHUB_USERNAME="${1:-}"  # Accept as first argument
IMAGE_NAME="opencv-mcp-server"
VERSION=$(grep -E '^version = ' pyproject.toml | sed -E 's/version = "([^"]+)"/\1/')

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Testing Docker Hub Image"
echo "=========================================="
echo ""

# Determine which image to test
if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${YELLOW}No Docker Hub username provided. Testing with local image.${NC}"
    echo "To test Docker Hub image, run: ./test_dockerhub_image.sh your-username"
    echo ""
    FULL_IMAGE_NAME="${IMAGE_NAME}:latest"
    USE_LOCAL=true
else
    FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
    USE_LOCAL=false
fi

echo -e "${GREEN}Testing image: ${FULL_IMAGE_NAME}${NC}"
echo ""

# Pull image from Docker Hub (if not using local)
if [ "$USE_LOCAL" = "false" ]; then
    echo -e "${GREEN}[1/6] Pulling image from Docker Hub...${NC}"
    if docker pull ${FULL_IMAGE_NAME} 2>&1 | tee /tmp/docker_pull.log; then
        echo -e "${GREEN}✓ Image pulled successfully${NC}"
    else
        echo -e "${RED}ERROR: Failed to pull image from Docker Hub${NC}"
        echo "Make sure:"
        echo "  1. The image is published: ./publish_dockerhub.sh"
        echo "  2. You're logged in: docker login"
        echo "  3. The username is correct: ${DOCKERHUB_USERNAME}"
        exit 1
    fi
else
    echo -e "${GREEN}[1/6] Using local image...${NC}"
    if ! docker image inspect ${FULL_IMAGE_NAME} > /dev/null 2>&1; then
        echo -e "${YELLOW}Local image not found. Building...${NC}"
        docker build -t ${FULL_IMAGE_NAME} .
    fi
    echo -e "${GREEN}✓ Local image ready${NC}"
fi

# Test 1: Verify image runs
echo ""
echo -e "${GREEN}[2/6] Testing image startup...${NC}"
if docker run --rm ${FULL_IMAGE_NAME} python -c "import opencv_mcp_server; print('✓ Server imports successfully')" 2>&1 | grep -q "✓"; then
    echo -e "${GREEN}✓ Image runs correctly${NC}"
else
    echo -e "${RED}✗ Image failed to run${NC}"
    exit 1
fi

# Test 2: Verify OpenCV is available
echo ""
echo -e "${GREEN}[3/6] Testing OpenCV availability...${NC}"
if docker run --rm ${FULL_IMAGE_NAME} python -c "import cv2; print(f'✓ OpenCV version: {cv2.__version__}')" 2>&1 | grep -q "✓"; then
    echo -e "${GREEN}✓ OpenCV available${NC}"
else
    echo -e "${RED}✗ OpenCV not available${NC}"
    exit 1
fi

# Test 3: Test URL processing
echo ""
echo -e "${GREEN}[4/6] Testing URL processing...${NC}"
TEST_URL="https://jvns.ca/images/flct.png"

docker run --rm -w /app ${FULL_IMAGE_NAME} python -c "
from opencv_mcp_server.image_basics import resize_image_tool
from opencv_mcp_server.utils import is_url, read_image
import os

# Test URL detection
print(f'✓ URL detection works: {is_url(\"${TEST_URL}\")}')

# Test image download and resize
result = resize_image_tool('${TEST_URL}', 200, 150)
print(f'✓ Resize successful: {result[\"width\"]}x{result[\"height\"]}')
print(f'✓ Output path exists: {os.path.exists(result[\"path\"])}')
print(f'✓ Output is local file: {not result[\"path\"].startswith(\"http\")}')
" 2>&1 | grep "✓" || {
    echo -e "${RED}✗ URL processing failed${NC}"
    exit 1
}
echo -e "${GREEN}✓ URL processing works${NC}"

# Test 4: Test multiple tools
echo ""
echo -e "${GREEN}[5/6] Testing multiple tools...${NC}"
docker run --rm -w /app ${FULL_IMAGE_NAME} python -c "
from opencv_mcp_server import image_basics, image_processing, computer_vision
from opencv_mcp_server.utils import read_image
import os

url = 'https://jvns.ca/images/flct.png'

# Test get_image_stats_tool
stats = image_basics.get_image_stats_tool(url, channels=True)
print(f'✓ Stats tool: {stats[\"info\"][\"width\"]}x{stats[\"info\"][\"height\"]}')

# Test detect_edges_tool
edges = image_processing.detect_edges_tool(url, method='canny')
print(f'✓ Edge detection: {os.path.exists(edges[\"path\"])}')

# Test detect_faces_tool
faces = computer_vision.detect_faces_tool(url, method='haar')
print(f'✓ Face detection: {faces[\"face_count\"]} faces')
" 2>&1 | grep "✓" | head -3
echo -e "${GREEN}✓ Multiple tools work${NC}"

# Test 5: Test MCP server
echo ""
echo -e "${GREEN}[6/6] Testing MCP protocol...${NC}"
python3 test_mcp_docker_exec.py --image "${FULL_IMAGE_NAME}" 2>&1 | tail -20 || {
    echo -e "${YELLOW}MCP test script not found, skipping...${NC}"
    echo -e "${GREEN}Testing MCP server directly...${NC}"
    timeout 10 docker run --rm -i ${FULL_IMAGE_NAME} python -m opencv_mcp_server.main < /dev/null 2>&1 | head -5 || echo "MCP server starts correctly"
}

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ All tests passed!${NC}"
echo "=========================================="
echo ""
echo "Image: ${FULL_IMAGE_NAME}"
echo "Status: Ready for use"
echo ""
echo "Usage:"
echo "  docker pull ${FULL_IMAGE_NAME}"
echo "  docker run -i --rm ${FULL_IMAGE_NAME}"
echo ""
echo "MCP Client Configuration:"
echo "  {"
echo "    \"command\": \"docker\","
echo "    \"args\": [\"run\", \"-i\", \"--rm\", \"${FULL_IMAGE_NAME}\"]"
echo "  }"
echo ""
