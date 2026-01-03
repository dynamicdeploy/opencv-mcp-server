# Quick Start: Publishing to Docker Hub

## One-Line Command

```bash
# Set your Docker Hub username and run
DOCKERHUB_USERNAME=your-username ./publish_dockerhub.sh
```

## Step-by-Step

1. **Login to Docker Hub** (if not already logged in):
   ```bash
   docker login
   ```

2. **Set your Docker Hub username** (optional, will prompt if not set):
   ```bash
   export DOCKERHUB_USERNAME=your-username
   ```

3. **Run the publish script**:
   ```bash
   ./publish_dockerhub.sh
   ```

4. **Confirm** when prompted (or set `NON_INTERACTIVE=true` for CI/CD)

## What Gets Published

The script will publish:
- `your-username/opencv-mcp-server:latest`
- `your-username/opencv-mcp-server:0.1.2` (version from pyproject.toml)
- `your-username/opencv-mcp-server:v0.1.2` (optional)

## After Publishing

Users can pull and use your image:

```bash
docker pull your-username/opencv-mcp-server:latest
docker run -i --rm your-username/opencv-mcp-server:latest
```

## CI/CD Usage

```bash
export DOCKERHUB_USERNAME=your-username
export NON_INTERACTIVE=true
./publish_dockerhub.sh
```

## Full Documentation

See `DOCKERHUB_PUBLISH.md` for complete documentation.

