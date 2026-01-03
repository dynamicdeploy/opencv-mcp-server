# Publishing to Docker Hub

This guide explains how to publish the OpenCV MCP Server Docker image to Docker Hub.

## Prerequisites

1. Docker installed and running
2. Docker Hub account
3. Logged in to Docker Hub (`docker login`)

## Quick Start

### Option 1: Use the publish script (Recommended)

```bash
# Set your Docker Hub username (optional, will prompt if not set)
export DOCKERHUB_USERNAME=your-username

# Run the publish script
./publish_dockerhub.sh
```

The script will:
1. Check Docker installation and login status
2. Build the Docker image
3. Tag it with your Docker Hub username
4. Push to Docker Hub with multiple tags:
   - `your-username/opencv-mcp-server:latest`
   - `your-username/opencv-mcp-server:0.1.2` (version from pyproject.toml)
   - `your-username/opencv-mcp-server:v0.1.2` (optional)

### Option 2: Manual publishing

```bash
# 1. Build the image
docker build -t opencv-mcp-server:latest .

# 2. Tag for Docker Hub (replace 'your-username' with your Docker Hub username)
docker tag opencv-mcp-server:latest your-username/opencv-mcp-server:latest
docker tag opencv-mcp-server:latest your-username/opencv-mcp-server:0.1.2

# 3. Push to Docker Hub
docker push your-username/opencv-mcp-server:latest
docker push your-username/opencv-mcp-server:0.1.2
```

## Docker Hub Login

If you're not logged in:

```bash
docker login
```

Enter your Docker Hub username and password when prompted.

## Using the Published Image

Once published, others can use your image:

```bash
# Pull the image
docker pull your-username/opencv-mcp-server:latest

# Run the MCP server
docker run -i --rm your-username/opencv-mcp-server:latest
```

## MCP Client Configuration

Users can configure their MCP clients to use your published image:

```json
{
  "mcpServers": {
    "opencv": {
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "your-username/opencv-mcp-server:latest"
      ]
    }
  }
}
```

## Versioning

The script automatically:
- Reads version from `pyproject.toml`
- Tags with version number (e.g., `0.1.2`)
- Tags with `v` prefix (e.g., `v0.1.2`)
- Always updates `latest` tag

## Troubleshooting

### Authentication Error

```bash
# Re-login to Docker Hub
docker logout
docker login
```

### Permission Denied

Make sure you're logged in with an account that has push permissions to the repository.

### Build Fails

Check that:
- Docker is running
- All dependencies are available
- Dockerfile is correct

## Automated Publishing (CI/CD)

For automated publishing in CI/CD pipelines:

```bash
# Set environment variables
export DOCKERHUB_USERNAME=your-username
export DOCKERHUB_PASSWORD=your-password  # Use secrets in CI/CD
export NON_INTERACTIVE=true

# Login non-interactively
echo "$DOCKERHUB_PASSWORD" | docker login -u "$DOCKERHUB_USERNAME" --password-stdin

# Run publish script (non-interactive mode)
./publish_dockerhub.sh
```

The script will skip all prompts when `NON_INTERACTIVE=true` is set.

### GitHub Actions Example

```yaml
name: Publish to Docker Hub

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Login to Docker Hub
        uses: docker/login-action@v2
        with:
          username: ${{ secrets.DOCKERHUB_USERNAME }}
          password: ${{ secrets.DOCKERHUB_PASSWORD }}
      
      - name: Publish to Docker Hub
        env:
          DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
          NON_INTERACTIVE: true
        run: ./publish_dockerhub.sh
```

