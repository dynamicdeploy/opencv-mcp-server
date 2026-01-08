# Troubleshooting Guide

## Common Issues

### Issue: Docker Pull Access Denied

**Error:**
```
docker: Error response from daemon: pull access denied for hackerdogs-mcp-ocr, 
repository does not exist or may require 'docker login'
```

**Cause:**
- Wrong image name in configuration
- The image name `hackerdogs-mcp-ocr` doesn't exist

**Solution:**
The correct image name is: `hackerdogs/opencv-mcp-server:latest`

Update your configuration to use:
```json
{
  "mcpServers": {
    "opencv-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "hackerdogs/opencv-mcp-server:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### Issue: Connection Closed Error

**Error:**
```
mcp.shared.exceptions.McpError: Connection closed
```

**Possible Causes:**
1. Docker container crashes on startup
2. Wrong Docker command arguments
3. Missing required flags (`-i` for interactive, `--rm` for cleanup)

**Solution:**
1. Verify the Docker command includes `-i` and `--rm` flags
2. Test the container manually:
   ```bash
   docker run -i --rm hackerdogs/opencv-mcp-server:latest
   ```
3. Check container logs for errors

### Issue: Image Not Found

**Error:**
```
Error response from daemon: pull access denied
```

**Solution:**
1. Verify image is public:
   ```bash
   docker pull hackerdogs/opencv-mcp-server:latest
   ```
2. If pull fails, check:
   - Internet connection
   - Docker Hub accessibility
   - Image name spelling (must be `hackerdogs/opencv-mcp-server`)

### Issue: MCP Server Not Starting

**Symptoms:**
- Connection closed immediately
- No response from server

**Solution:**
1. Test server manually:
   ```bash
   echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | \
   docker run -i --rm hackerdogs/opencv-mcp-server:latest python3 -m opencv_mcp_server.main
   ```

2. Check for Python errors in container logs

3. Verify environment variables:
   ```bash
   docker run -i --rm \
     -e MCP_TRANSPORT=stdio \
     -e PYTHONUNBUFFERED=1 \
     hackerdogs/opencv-mcp-server:latest
   ```

## Verification Steps

### 1. Verify Image is Public
```bash
docker pull hackerdogs/opencv-mcp-server:latest
```

### 2. Test Container Startup
```bash
docker run --rm hackerdogs/opencv-mcp-server:latest echo "Container works"
```

### 3. Test MCP Server
```bash
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}}' | \
docker run -i --rm hackerdogs/opencv-mcp-server:latest python3 -m opencv_mcp_server.main
```

### 4. Test Tool Listing
```bash
echo '{"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}' | \
docker run -i --rm hackerdogs/opencv-mcp-server:latest python3 -m opencv_mcp_server.main
```

## Correct Configuration

### For MCP Clients (Claude Desktop, Cursor)
```json
{
  "mcpServers": {
    "opencv-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "hackerdogs/opencv-mcp-server:latest"
      ],
      "env": {
        "MCP_TRANSPORT": "stdio",
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

### For Programmatic Use (Python)
```python
import subprocess

docker_cmd = [
    "docker", "run", "-i", "--rm",
    "hackerdogs/opencv-mcp-server:latest"
]

process = subprocess.Popen(
    docker_cmd,
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
```

## Image Information

- **Repository:** `hackerdogs/opencv-mcp-server`
- **Latest Tag:** `latest`
- **Current Version:** `0.1.5`
- **Size:** ~1.1GB
- **Status:** Public and accessible

## Getting Help

If issues persist:
1. Check Docker logs: `docker logs <container_id>`
2. Verify image exists: `docker images | grep opencv-mcp-server`
3. Test with a simple command first
4. Check network connectivity to Docker Hub


