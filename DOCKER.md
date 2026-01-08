# Docker Usage Guide

This guide explains how to build and use the OpenCV MCP Server Docker image.

## Building the Docker Image

To build the Docker image, run:

```bash
docker build -t opencv-mcp-server:latest .
```

## Running the Docker Container

The MCP server can be run in Docker and supports both local files (via volume mounts) and URLs.

### Basic Usage

Run the MCP server container:

```bash
docker run -it --rm opencv-mcp-server:latest
```

### Using with Local Files

To process local files, mount a directory containing your images/videos:

```bash
docker run -it --rm \
  -v /path/to/your/data:/data/input \
  -v /path/to/output:/data/output \
  opencv-mcp-server:latest
```

Then reference files as `/data/input/your-image.jpg` when calling MCP tools.

### Using with URLs

The server now supports image URLs directly. You can pass URLs to any image processing function:

```bash
# Example: Process an image from a URL
docker exec <container_id> python -c "
from opencv_mcp_server.image_basics import resize_image_tool
result = resize_image_tool(
    image_path='https://example.com/image.jpg',
    width=800,
    height=600
)
print(result)
"
```

### Using with MCP Client

When using with an MCP client (like Claude Desktop), you can configure it to use Docker:

```json
{
  "mcpServers": {
    "opencv": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-v", "/path/to/data:/data/input",
        "opencv-mcp-server:latest"
      ]
    }
  }
}
```

### Environment Variables

You can customize the Docker container behavior with environment variables:

- `MCP_TRANSPORT`: Transport method (default: "stdio")
- `OPENCV_DNN_MODELS_DIR`: Directory for DNN models (default: "/app/OPENCV_DNN_MODELS_DIR")
- `PYTHONUNBUFFERED`: Set to 1 for unbuffered output (default: 1)

Example:

```bash
docker run -it --rm \
  -e MCP_TRANSPORT=stdio \
  -e OPENCV_DNN_MODELS_DIR=/app/models \
  opencv-mcp-server:latest
```

## Examples

### Example 1: Resize an Image from URL

```bash
docker run -it --rm opencv-mcp-server:latest python -c "
from opencv_mcp_server.image_basics import resize_image_tool
result = resize_image_tool(
    image_path='https://example.com/photo.jpg',
    width=800,
    height=600
)
print(f'Resized image saved to: {result[\"path\"]}')
"
```

### Example 2: Detect Faces in an Image from URL

```bash
docker run -it --rm opencv-mcp-server:latest python -c "
from opencv_mcp_server.computer_vision import detect_faces_tool
result = detect_faces_tool(
    image_path='https://example.com/group-photo.jpg',
    method='dnn',
    confidence_threshold=0.5
)
print(f'Found {result[\"face_count\"]} faces')
"
```

### Example 3: Process Local File

```bash
# Mount your data directory
docker run -it --rm \
  -v $(pwd)/images:/data/input \
  opencv-mcp-server:latest python -c "
from opencv_mcp_server.image_processing import detect_edges_tool
result = detect_edges_tool(
    image_path='/data/input/my-image.jpg',
    method='canny',
    threshold1=100,
    threshold2=200
)
print(f'Edge detection complete: {result[\"path\"]}')
"
```

## Notes

- The Docker image includes all required OpenCV dependencies and model files
- Temporary files downloaded from URLs are stored in the container's temp directory
- For persistent storage, use volume mounts for input/output directories
- The container runs as a non-root user for security
- Image URLs are automatically downloaded and processed

## Troubleshooting

### Container exits immediately

The MCP server runs in stdio mode by default. Make sure you're connecting it to an MCP client or using it interactively.

### Cannot access local files

Ensure you've mounted the correct directories with the `-v` flag and that file paths reference the mounted locations (e.g., `/data/input/...`).

### URL download fails

Check that:
- The URL is accessible
- The image format is supported (JPEG, PNG, GIF, WebP)
- Network connectivity is available in the container


