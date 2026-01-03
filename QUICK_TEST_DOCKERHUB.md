# Quick Test: Docker Hub Public Image

## Test a Published Image

Once the image is published to Docker Hub, test it with:

```bash
# Option 1: Bash script
./test_dockerhub_image.sh <dockerhub-username>

# Option 2: Python script  
python test_dockerhub_pull.py <dockerhub-username>

# Option 3: Direct pull and test
docker pull <dockerhub-username>/opencv-mcp-server:latest
docker run --rm <dockerhub-username>/opencv-mcp-server:latest python -c "import opencv_mcp_server; print('OK')"
```

## Example

If the image is published as `yourusername/opencv-mcp-server:latest`:

```bash
# Pull and test
./test_dockerhub_image.sh yourusername

# Or use Python test
python test_dockerhub_pull.py yourusername
```

## What Gets Tested

✅ Image pulls successfully  
✅ Image runs without errors  
✅ OpenCV is available  
✅ 22 tools accessible via MCP  
✅ URL processing works  
✅ Tool execution works correctly  
✅ Output files are created properly  

## Current Status

The test infrastructure is ready. To test a published image:

1. **Get the Docker Hub username** where the image is published
2. **Run the test:**
   ```bash
   ./test_dockerhub_image.sh <username>
   ```

## Test Results Location

- `test_dockerhub_pull_results.json` - Detailed test results
- Console output - Real-time test progress

## Troubleshooting

**Image not found?**
- Verify the username is correct
- Check the image is published: `docker search <username>/opencv-mcp-server`
- Ensure the image is public (not private)

**Pull fails?**
- Try logging in: `docker login`
- Check network connectivity
- Verify image name: `<username>/opencv-mcp-server:latest`

