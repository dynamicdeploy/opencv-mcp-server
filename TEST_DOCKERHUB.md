# Testing Docker Hub Image

This guide explains how to test the OpenCV MCP Server image after publishing to Docker Hub.

## Quick Test

### Test with Local Image (Before Publishing)

```bash
# Test local image
./test_dockerhub_image.sh

# Or use Python test
python test_dockerhub_pull.py
# Enter 'local' when prompted
```

### Test After Publishing to Docker Hub

```bash
# Test with Docker Hub username
./test_dockerhub_image.sh your-username

# Or use Python test
python test_dockerhub_pull.py your-username
```

## Test Scripts

### 1. `test_dockerhub_image.sh`

Bash script that tests the Docker image comprehensively:

```bash
# Test local image
./test_dockerhub_image.sh

# Test Docker Hub image
./test_dockerhub_image.sh your-username
```

**Tests performed:**
- ✅ Image startup
- ✅ OpenCV availability
- ✅ URL processing
- ✅ Multiple tools (stats, resize, edges, faces)
- ✅ MCP protocol

### 2. `test_dockerhub_pull.py`

Python script that tests via MCP client:

```bash
# Test local image
python test_dockerhub_pull.py local

# Test Docker Hub image
python test_dockerhub_pull.py your-username
```

**Tests performed:**
- ✅ Pull image from Docker Hub
- ✅ List tools via MCP
- ✅ Process images from URLs
- ✅ Verify output files

## Manual Testing

### Step 1: Pull Image

```bash
docker pull your-username/opencv-mcp-server:latest
```

### Step 2: Test Basic Functionality

```bash
# Test imports
docker run --rm your-username/opencv-mcp-server:latest \
  python -c "import opencv_mcp_server; print('OK')"

# Test OpenCV
docker run --rm your-username/opencv-mcp-server:latest \
  python -c "import cv2; print(f'OpenCV {cv2.__version__}')"
```

### Step 3: Test URL Processing

```bash
docker run --rm -w /app your-username/opencv-mcp-server:latest python -c "
from opencv_mcp_server.image_basics import resize_image_tool
result = resize_image_tool('https://jvns.ca/images/flct.png', 200, 150)
print(f'Resized: {result[\"width\"]}x{result[\"height\"]}')
print(f'Output: {result[\"path\"]}')
"
```

### Step 4: Test MCP Protocol

```bash
# Use the MCP client test
python test_mcp_docker_exec.py
```

## Expected Results

After pulling and testing, you should see:

✅ **Image pulls successfully**
✅ **22 tools available via MCP**
✅ **URL processing works correctly**
✅ **Output files are created locally (not URLs)**
✅ **All operations produce correct results**

## Troubleshooting

### Image Not Found

If you get "image not found" error:
1. Make sure you've published the image: `./publish_dockerhub.sh`
2. Check the username is correct
3. Verify you're logged in: `docker login`

### Pull Fails

```bash
# Re-login to Docker Hub
docker logout
docker login

# Try pulling again
docker pull your-username/opencv-mcp-server:latest
```

### MCP Tests Fail

Make sure:
1. Image is running correctly
2. MCP client is installed: `pip install mcp`
3. Network connectivity for URL downloads

## Verification Checklist

- [ ] Image pulls from Docker Hub
- [ ] Image runs without errors
- [ ] OpenCV is available
- [ ] 22 tools are accessible via MCP
- [ ] URL processing works
- [ ] Output files are created correctly
- [ ] MCP protocol communication works
- [ ] All test scripts pass

## Test Results

After running tests, results are saved to:
- `test_dockerhub_pull_results.json`
- `test_mcp_docker_exec_results.json`

