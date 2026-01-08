# Debugging MCP Docker Error

## Error Analysis

**Error Message:**
```
docker: Error response from daemon: pull access denied for hackerdogs-mcp-ocr, 
repository does not exist or may require 'docker login'
```

## Root Cause

The LLM is **NOT** making this up. The error is from the Docker daemon, which means:

1. **Your application is executing a Docker command** with the wrong image name
2. **The image name `hackerdogs-mcp-ocr` is in your application's configuration**
3. **This is NOT coming from the LLM** - LLMs don't modify Docker commands

## Where to Look

### 1. Multiple MCP Server Configurations

You likely have **multiple MCP servers** configured, and one has the wrong image name:

```json
{
  "mcpServers": {
    "opencv-mcp-server": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs/opencv-mcp-server:latest"]
    },
    "mcp-ocr": {  // ← THIS ONE HAS WRONG IMAGE NAME
      "command": "docker",
      "args": ["run", "-i", "--rm", "hackerdogs-mcp-ocr"]  // ← WRONG!
    }
  }
}
```

### 2. Database/Configuration Storage

If your application stores MCP configs in a database:

```sql
-- Check for MCP server configurations
SELECT * FROM mcp_servers WHERE name LIKE '%ocr%';
SELECT * FROM mcp_servers WHERE docker_image LIKE '%ocr%';
```

### 3. Environment Variables

Check for environment variables that might override config:

```bash
env | grep -i mcp
env | grep -i ocr
env | grep -i docker
```

### 4. Code That Constructs Docker Commands

Search your codebase for where Docker commands are built:

```bash
# In your hackerdogs-core directory
grep -r "hackerdogs-mcp-ocr" .
grep -r "mcp-ocr" .
grep -r "docker.*run.*mcp" .
```

### 5. Configuration Files

Check all configuration files:

- `~/.config/claude/claude_desktop_config.json`
- `~/Library/Application Support/Claude/claude_desktop_config.json`
- Application-specific config files
- Database configuration tables

## How to Fix

### Step 1: Find the Source

```bash
# Search your entire codebase
cd /path/to/hackerdogs-core
grep -r "hackerdogs-mcp-ocr" .
grep -r "mcp-ocr" .
```

### Step 2: Check Your MCP Configuration

Look for all MCP server entries:

```python
# In your application code
mcp_servers = get_all_mcp_servers()  # Your function
for server in mcp_servers:
    print(f"Server: {server.name}")
    print(f"Image: {server.docker_image}")
    print(f"Command: {server.command}")
```

### Step 3: Fix the Configuration

Once you find where `hackerdogs-mcp-ocr` is configured:

1. **If it's a separate OCR MCP server:**
   - Either remove it if not needed
   - Or fix the image name to the correct OCR server image
   - Or create the `hackerdogs-mcp-ocr` image if it should exist

2. **If it's a typo:**
   - Change `hackerdogs-mcp-ocr` to `hackerdogs/opencv-mcp-server:latest`
   - Or whatever the correct image name should be

## Verification

After fixing, verify:

```bash
# Test the Docker command directly
docker run -i --rm hackerdogs/opencv-mcp-server:latest echo "test"

# Check your application logs
# The error should disappear once the config is fixed
```

## Why This Happens

The error occurs because:

1. Your application loads MCP server configurations
2. It tries to start ALL configured MCP servers
3. One server (OCR) has wrong image name
4. Docker fails to pull that image
5. The MCP client connection fails
6. This causes the "Connection closed" error

## The OpenCV Server is Fine

The OpenCV MCP server configuration is **correct**:
- ✅ Image name: `hackerdogs/opencv-mcp-server:latest`
- ✅ Image is public and accessible
- ✅ Server works when tested directly

The issue is with a **different MCP server** (likely OCR) that has the wrong configuration.


