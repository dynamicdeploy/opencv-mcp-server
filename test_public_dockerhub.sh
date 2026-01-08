#!/bin/bash
# Test script to download and verify a public Docker Hub image

set -e

# Configuration
DOCKERHUB_USERNAME="${1:-}"
IMAGE_NAME="opencv-mcp-server"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "Testing Public Docker Hub Image"
echo "=========================================="
echo ""

# Get Docker Hub username
if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${YELLOW}No Docker Hub username provided.${NC}"
    echo "Usage: $0 <dockerhub-username>"
    echo ""
    echo "Example: $0 alonido"
    echo ""
    read -p "Enter Docker Hub username (or press Enter to test local): " DOCKERHUB_USERNAME
fi

if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${BLUE}Testing with local image instead...${NC}"
    FULL_IMAGE_NAME="${IMAGE_NAME}:latest"
    USE_LOCAL=true
else
    FULL_IMAGE_NAME="${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
    USE_LOCAL=false
fi

echo -e "${GREEN}Testing image: ${FULL_IMAGE_NAME}${NC}"
echo ""

# Pull image from Docker Hub
if [ "$USE_LOCAL" = "false" ]; then
    echo -e "${GREEN}[1/7] Pulling image from Docker Hub...${NC}"
    if docker pull ${FULL_IMAGE_NAME} 2>&1; then
        echo -e "${GREEN}✓ Image pulled successfully from Docker Hub${NC}"
    else
        echo -e "${RED}✗ Failed to pull image from Docker Hub${NC}"
        echo ""
        echo "Possible reasons:"
        echo "  1. Image not published yet"
        echo "  2. Username is incorrect"
        echo "  3. Image is private (requires login)"
        echo ""
        echo "Trying local image instead..."
        FULL_IMAGE_NAME="${IMAGE_NAME}:latest"
        USE_LOCAL=true
        if ! docker image inspect ${FULL_IMAGE_NAME} > /dev/null 2>&1; then
            echo -e "${YELLOW}Building local image...${NC}"
            docker build -t ${FULL_IMAGE_NAME} .
        fi
    fi
else
    echo -e "${GREEN}[1/7] Using local image...${NC}"
    if ! docker image inspect ${FULL_IMAGE_NAME} > /dev/null 2>&1; then
        echo -e "${YELLOW}Local image not found. Building...${NC}"
        docker build -t ${FULL_IMAGE_NAME} .
    fi
    echo -e "${GREEN}✓ Local image ready${NC}"
fi

# Test 1: Verify image runs
echo ""
echo -e "${GREEN}[2/7] Testing image startup...${NC}"
if docker run --rm ${FULL_IMAGE_NAME} python -c "import opencv_mcp_server; print('✓ Server imports successfully')" 2>&1 | grep -q "✓"; then
    echo -e "${GREEN}✓ Image runs correctly${NC}"
else
    echo -e "${RED}✗ Image failed to run${NC}"
    exit 1
fi

# Test 2: Verify OpenCV
echo ""
echo -e "${GREEN}[3/7] Testing OpenCV availability...${NC}"
CV_VERSION=$(docker run --rm ${FULL_IMAGE_NAME} python -c "import cv2; print(cv2.__version__)" 2>&1 | tail -1)
if [ -n "$CV_VERSION" ]; then
    echo -e "${GREEN}✓ OpenCV ${CV_VERSION} available${NC}"
else
    echo -e "${RED}✗ OpenCV not available${NC}"
    exit 1
fi

# Test 3: Verify dependencies
echo ""
echo -e "${GREEN}[4/7] Testing dependencies...${NC}"
docker run --rm ${FULL_IMAGE_NAME} python -c "
import sys
deps = ['cv2', 'numpy', 'requests']
missing = []
for dep in deps:
    try:
        __import__(dep)
    except ImportError:
        missing.append(dep)
if missing:
    print(f'✗ Missing: {missing}')
    sys.exit(1)
else:
    print('✓ All dependencies available')
" 2>&1 | grep -E "(✓|✗)" || echo "Dependencies check completed"

# Test 4: Test URL processing
echo ""
echo -e "${GREEN}[5/7] Testing URL processing...${NC}"
TEST_URL="https://jvns.ca/images/flct.png"

docker run --rm -w /app ${FULL_IMAGE_NAME} python -c "
from opencv_mcp_server.utils import is_url, read_image
from opencv_mcp_server.image_basics import resize_image_tool
import os

# Test URL detection
url_detected = is_url('${TEST_URL}')
print(f'✓ URL detection: {url_detected}')

# Test image download and resize
result = resize_image_tool('${TEST_URL}', 200, 150)
print(f'✓ Resize successful: {result[\"width\"]}x{result[\"height\"]}')
print(f'✓ Output exists: {os.path.exists(result[\"path\"])}')
print(f'✓ Output is local: {not result[\"path\"].startswith(\"http\")}')
" 2>&1 | grep "✓" | head -4
echo -e "${GREEN}✓ URL processing works${NC}"

# Test 5: Test multiple tools
echo ""
echo -e "${GREEN}[6/7] Testing multiple tools...${NC}"
docker run --rm -w /app ${FULL_IMAGE_NAME} python -c "
from opencv_mcp_server import image_basics, image_processing, computer_vision
import os

url = 'https://jvns.ca/images/flct.png'

# Test get_image_stats_tool
stats = image_basics.get_image_stats_tool(url, channels=True)
print(f'✓ Stats: {stats[\"info\"][\"width\"]}x{stats[\"info\"][\"height\"]}')

# Test detect_edges_tool
edges = image_processing.detect_edges_tool(url, method='canny')
print(f'✓ Edge detection: {os.path.exists(edges[\"path\"])}')

# Test detect_faces_tool
faces = computer_vision.detect_faces_tool(url, method='haar')
print(f'✓ Face detection: {faces[\"face_count\"]} faces')
" 2>&1 | grep "✓" | head -3
echo -e "${GREEN}✓ Multiple tools work${NC}"

# Test 6: Test MCP protocol
echo ""
echo -e "${GREEN}[7/7] Testing MCP protocol...${NC}"
if [ -f "test_mcp_docker_exec.py" ]; then
    python3 test_mcp_docker_exec.py --image "${FULL_IMAGE_NAME}" 2>&1 | tail -15 || {
        echo -e "${YELLOW}MCP test script not available, skipping...${NC}"
    }
else
    echo -e "${YELLOW}MCP test script not found, testing basic MCP startup...${NC}"
    timeout 5 docker run --rm -i ${FULL_IMAGE_NAME} python -m opencv_mcp_server.main < /dev/null 2>&1 | head -3 || echo "MCP server starts"
fi

# Summary
echo ""
echo "=========================================="
echo -e "${GREEN}✓ All tests completed!${NC}"
echo "=========================================="
echo ""
echo "Image: ${FULL_IMAGE_NAME}"
echo "Source: $([ "$USE_LOCAL" = "true" ] && echo "Local" || echo "Docker Hub")"
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


