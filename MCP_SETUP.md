# MCP Server Configuration Guide

This guide explains how to add the OpenCV MCP Server to Cursor or Claude Desktop.

## Docker Hub Image

The server is available as a Docker image:
- **Image:** `hackerdogs/opencv-mcp-server:latest`
- **Pull command:** `docker pull hackerdogs/opencv-mcp-server:latest`

## Configuration Files

### For Claude Desktop

1. **Locate the configuration file:**
   - **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux:** `~/.config/Claude/claude_desktop_config.json`

2. **Add the server configuration:**

   Open the config file and add the OpenCV MCP server to the `mcpServers` section:

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

3. **Restart Claude Desktop** for changes to take effect.

### For Cursor

1. **Locate the configuration file:**
   - The MCP configuration in Cursor is typically in the settings or a similar location
   - Check Cursor's documentation for the exact location

2. **Add the server configuration:**

   Use the same configuration as Claude Desktop:

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

3. **Restart Cursor** for changes to take effect.

## Quick Setup Script

You can use the provided configuration file:

```bash
# For Claude Desktop (macOS)
cp claude_desktop_config.json ~/Library/Application\ Support/Claude/claude_desktop_config.json

# For Claude Desktop (Windows)
# Copy claude_desktop_config.json to %APPDATA%\Claude\claude_desktop_config.json

# For Claude Desktop (Linux)
cp claude_desktop_config.json ~/.config/Claude/claude_desktop_config.json
```

**Note:** If you already have an MCP configuration file, merge the `opencv-mcp-server` entry into your existing `mcpServers` object.

## Prerequisites

1. **Docker must be installed and running:**
   ```bash
   docker --version
   ```

2. **Pull the Docker image (optional, will auto-pull if not present):**
   ```bash
   docker pull hackerdogs/opencv-mcp-server:latest
   ```

## Verification

After adding the configuration:

1. Restart your application (Cursor or Claude Desktop)
2. Check that the MCP server is connected
3. Try using one of the OpenCV tools:
   - `get_image_stats_tool` - Get image statistics
   - `resize_image_tool` - Resize images
   - `detect_edges_tool` - Detect edges
   - `detect_faces_tool` - Detect faces
   - And 18 more tools!

## Available Tools

The OpenCV MCP Server provides 22 tools:

### Image Basics
- `get_image_stats_tool` - Get image statistics
- `resize_image_tool` - Resize images
- `crop_image_tool` - Crop images
- `rotate_image_tool` - Rotate images
- `flip_image_tool` - Flip images
- `convert_image_format_tool` - Convert image formats

### Image Processing
- `detect_edges_tool` - Detect edges (Canny, Sobel, Laplacian)
- `apply_filter_tool` - Apply filters (blur, sharpen, etc.)
- `adjust_brightness_contrast_tool` - Adjust brightness/contrast
- `apply_threshold_tool` - Apply thresholding
- `find_contours_tool` - Find contours
- `morphological_operations_tool` - Morphological operations

### Computer Vision
- `detect_faces_tool` - Detect faces (Haar, DNN)
- `detect_objects_tool` - Detect objects (YOLO)
- `detect_features_tool` - Detect features (SIFT, ORB, etc.)
- `match_features_tool` - Match features
- `detect_corners_tool` - Detect corners

### Video Processing
- `extract_frames_tool` - Extract frames from video
- `process_video_tool` - Process video
- `detect_motion_tool` - Detect motion
- `track_objects_tool` - Track objects

## Troubleshooting

### Docker not found
- Ensure Docker is installed and running
- Check Docker is in your PATH: `which docker`

### Image pull fails
- Check internet connection
- Verify Docker Hub access: `docker pull hello-world`
- Try pulling manually: `docker pull hackerdogs/opencv-mcp-server:latest`

### Server not connecting
- Check Docker is running: `docker ps`
- Verify image exists: `docker images | grep opencv-mcp-server`
- Check application logs for errors
- Ensure the configuration JSON is valid

### Tools not available
- Restart the application after configuration changes
- Check MCP server connection status
- Verify Docker container can run: `docker run --rm hackerdogs/opencv-mcp-server:latest python -c "import opencv_mcp_server"`

## Support

For issues or questions:
- GitHub: https://github.com/gongrzhe/opencv-mcp-server
- Docker Hub: https://hub.docker.com/r/hackerdogs/opencv-mcp-server


