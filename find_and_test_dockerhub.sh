#!/bin/bash
# Script to find and test the public Docker Hub image

set -e

# Try common usernames based on git remotes
POSSIBLE_USERNAMES=("alonido" "dynamicdeploy" "gongrzhe" "tredkar")

echo "=========================================="
echo "Finding and Testing Docker Hub Image"
echo "=========================================="
echo ""

FOUND_IMAGE=""
FOUND_USERNAME=""

# Try to find the image
for username in "${POSSIBLE_USERNAMES[@]}"; do
    echo -n "Trying ${username}/opencv-mcp-server:latest... "
    if docker pull ${username}/opencv-mcp-server:latest 2>&1 | grep -q "Downloaded\|Image is up to date"; then
        FOUND_IMAGE="${username}/opencv-mcp-server:latest"
        FOUND_USERNAME="${username}"
        echo "✓ FOUND!"
        break
    else
        echo "✗ Not found"
    fi
done

# If not found, ask user
if [ -z "$FOUND_IMAGE" ]; then
    echo ""
    echo "Could not find image automatically."
    read -p "Enter Docker Hub username (or 'local' to test local): " USERNAME
    
    if [ "$USERNAME" != "local" ] && [ -n "$USERNAME" ]; then
        echo "Trying ${USERNAME}/opencv-mcp-server:latest..."
        if docker pull ${USERNAME}/opencv-mcp-server:latest 2>&1 | grep -q "Downloaded\|Image is up to date"; then
            FOUND_IMAGE="${USERNAME}/opencv-mcp-server:latest"
            FOUND_USERNAME="${USERNAME}"
            echo "✓ Found!"
        else
            echo "✗ Not found. Using local image instead."
            FOUND_IMAGE="opencv-mcp-server:latest"
        fi
    else
        FOUND_IMAGE="opencv-mcp-server:latest"
    fi
fi

echo ""
echo "Testing image: ${FOUND_IMAGE}"
echo ""

# Run comprehensive tests
if [ -f "test_dockerhub_image.sh" ]; then
    if [ "$FOUND_USERNAME" != "" ]; then
        ./test_dockerhub_image.sh ${FOUND_USERNAME}
    else
        ./test_dockerhub_image.sh
    fi
elif [ -f "test_public_dockerhub.sh" ]; then
    if [ "$FOUND_USERNAME" != "" ]; then
        echo "" | ./test_public_dockerhub.sh ${FOUND_USERNAME}
    else
        echo "" | ./test_public_dockerhub.sh
    fi
else
    echo "Running basic tests..."
    docker run --rm ${FOUND_IMAGE} python -c "import opencv_mcp_server; print('✓ OK')"
fi

