#!/bin/bash
# Script to build and publish OpenCV MCP Server to Docker Hub

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="opencv-mcp-server"
VERSION=$(grep -E '^version = ' pyproject.toml | sed -E 's/version = "([^"]+)"/\1/')
DOCKERHUB_USERNAME="${DOCKERHUB_USERNAME:-}"  # Set via environment variable or prompt
NON_INTERACTIVE="${NON_INTERACTIVE:-false}"  # Set to true for CI/CD
BUILD_IMAGE=false  # Default: don't build, assume image exists

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --build)
            BUILD_IMAGE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--build]"
            echo ""
            echo "Options:"
            echo "  --build    Build the Docker image before publishing"
            echo "  --help     Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  DOCKERHUB_USERNAME    Docker Hub username (required)"
            echo "  NON_INTERACTIVE       Set to 'true' for CI/CD (default: false)"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "=========================================="
echo "OpenCV MCP Server - Docker Hub Publisher"
echo "=========================================="
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed or not in PATH${NC}"
    exit 1
fi

# Check if user is logged in to Docker Hub
if ! docker info 2>/dev/null | grep -q "Username:"; then
    if [ "$NON_INTERACTIVE" = "true" ]; then
        echo -e "${RED}ERROR: Not logged in to Docker Hub and NON_INTERACTIVE=true${NC}"
        echo "Please login first with: docker login"
        exit 1
    fi
    echo -e "${YELLOW}WARNING: Not logged in to Docker Hub${NC}"
    echo "Please login first with: docker login"
    read -p "Do you want to login now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker login
    else
        echo -e "${RED}Cannot proceed without Docker Hub login${NC}"
        exit 1
    fi
fi

# Get Docker Hub username if not set
if [ -z "$DOCKERHUB_USERNAME" ]; then
    # Try to get from docker info
    DOCKERHUB_USERNAME=$(docker info 2>/dev/null | grep "Username:" | awk '{print $2}' || echo "")
    
    if [ -z "$DOCKERHUB_USERNAME" ]; then
        if [ "$NON_INTERACTIVE" = "true" ]; then
            echo -e "${RED}ERROR: DOCKERHUB_USERNAME not set and NON_INTERACTIVE=true${NC}"
            echo "Please set DOCKERHUB_USERNAME environment variable"
            exit 1
        fi
        echo -e "${YELLOW}Docker Hub username not found${NC}"
        read -p "Enter your Docker Hub username: " DOCKERHUB_USERNAME
    fi
fi

if [ -z "$DOCKERHUB_USERNAME" ]; then
    echo -e "${RED}ERROR: Docker Hub username is required${NC}"
    exit 1
fi

echo -e "${GREEN}Using Docker Hub username: ${DOCKERHUB_USERNAME}${NC}"
echo -e "${GREEN}Image version: ${VERSION}${NC}"
echo ""

# Confirm before proceeding (skip in non-interactive mode)
if [ "$NON_INTERACTIVE" != "true" ]; then
    echo "This will:"
    if [ "$BUILD_IMAGE" = "true" ]; then
        echo "  1. Build Docker image: ${IMAGE_NAME}:latest"
        echo "  2. Tag as: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
        echo "  3. Tag as: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
        echo "  4. Push both tags to Docker Hub"
    else
        echo "  1. Tag existing image: ${IMAGE_NAME}:latest"
        echo "  2. Tag as: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
        echo "  3. Tag as: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
        echo "  4. Push both tags to Docker Hub"
    fi
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi
fi

# Build the image if --build flag is set
if [ "$BUILD_IMAGE" = "true" ]; then
    echo ""
    echo -e "${GREEN}[1/4] Building Docker image...${NC}"
    
    # Check if build.sh exists and use it, otherwise build directly
    if [ -f "build.sh" ]; then
        echo "Using build.sh script..."
        bash build.sh
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Build script failed${NC}"
            exit 1
        fi
    else
        docker build -t ${IMAGE_NAME}:latest .
        if [ $? -ne 0 ]; then
            echo -e "${RED}ERROR: Docker build failed${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ Build successful${NC}"
    fi
else
    # Check if image exists
    if ! docker image inspect ${IMAGE_NAME}:latest > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Image ${IMAGE_NAME}:latest not found${NC}"
        echo "Please build the image first with:"
        echo "  ./build.sh"
        echo "  OR"
        echo "  $0 --build"
        exit 1
    fi
    echo ""
    echo -e "${GREEN}[1/4] Using existing image: ${IMAGE_NAME}:latest${NC}"
    echo -e "${GREEN}✓ Image found${NC}"
fi

# Tag for Docker Hub
echo ""
if [ "$BUILD_IMAGE" = "true" ]; then
    echo -e "${GREEN}[2/4] Tagging images...${NC}"
else
    echo -e "${GREEN}[1/3] Tagging images...${NC}"
fi

# Tag as latest
docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest
echo -e "${GREEN}✓ Tagged: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest${NC}"

# Tag with version
docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}
echo -e "${GREEN}✓ Tagged: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"

# Optional: Tag as 'v{version}' if version doesn't start with 'v'
if [[ ! "$VERSION" =~ ^v ]]; then
    docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:v${VERSION}
    echo -e "${GREEN}✓ Tagged: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:v${VERSION}${NC}"
fi

# Push to Docker Hub
echo ""
if [ "$BUILD_IMAGE" = "true" ]; then
    echo -e "${GREEN}[3/4] Pushing images to Docker Hub...${NC}"
else
    echo -e "${GREEN}[2/3] Pushing images to Docker Hub...${NC}"
fi

# Push latest
echo "Pushing ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest..."
docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to push latest tag${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Pushed: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest${NC}"

# Push version tag
echo "Pushing ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}..."
docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}

if [ $? -ne 0 ]; then
    echo -e "${RED}ERROR: Failed to push version tag${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Pushed: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}${NC}"

# Push v{version} tag if created
if [[ ! "$VERSION" =~ ^v ]]; then
    echo "Pushing ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:v${VERSION}..."
    docker push ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:v${VERSION}
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Pushed: ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:v${VERSION}${NC}"
    fi
fi

# Summary
echo ""
if [ "$BUILD_IMAGE" = "true" ]; then
    echo -e "${GREEN}[4/4] Summary${NC}"
else
    echo -e "${GREEN}[3/3] Summary${NC}"
fi
echo "=========================================="
echo -e "${GREEN}✓ Successfully published to Docker Hub!${NC}"
echo ""
echo "Image tags:"
echo "  - ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
echo "  - ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:${VERSION}"
if [[ ! "$VERSION" =~ ^v ]]; then
    echo "  - ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:v${VERSION}"
fi
echo ""
echo "Usage:"
echo "  docker pull ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
echo "  docker run -i --rm ${DOCKERHUB_USERNAME}/${IMAGE_NAME}:latest"
echo ""
echo "=========================================="

