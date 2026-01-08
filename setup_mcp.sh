#!/bin/bash
# Quick setup script for adding OpenCV MCP Server to Claude Desktop or Cursor

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "=========================================="
echo "OpenCV MCP Server - Quick Setup"
echo "=========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    CLAUDE_CONFIG="$HOME/.config/Claude/claude_desktop_config.json"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    OS="windows"
    CLAUDE_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
else
    OS="unknown"
    CLAUDE_CONFIG=""
fi

echo -e "${BLUE}Detected OS: ${OS}${NC}"
echo ""

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not installed or not in PATH${NC}"
    echo "Please install Docker first: https://www.docker.com/get-started"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}ERROR: Docker is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker is installed and running${NC}"
echo ""

# Pull Docker image
echo -e "${YELLOW}Pulling Docker image...${NC}"
if docker pull hackerdogs/opencv-mcp-server:latest 2>&1 | grep -q "Downloaded\|Image is up to date\|Pulling"; then
    echo -e "${GREEN}✓ Docker image pulled successfully${NC}"
else
    echo -e "${YELLOW}⚠ Could not pull image (will be pulled automatically when needed)${NC}"
fi
echo ""

# Setup for Claude Desktop
echo -e "${BLUE}Setting up for Claude Desktop...${NC}"

if [ -z "$CLAUDE_CONFIG" ]; then
    echo -e "${YELLOW}⚠ Could not determine Claude Desktop config location for your OS${NC}"
    echo "Please manually copy claude_desktop_config.json to your Claude Desktop config directory"
else
    CLAUDE_DIR=$(dirname "$CLAUDE_CONFIG")
    
    # Create directory if it doesn't exist
    if [ ! -d "$CLAUDE_DIR" ]; then
        echo "Creating Claude Desktop config directory..."
        mkdir -p "$CLAUDE_DIR"
    fi
    
    # Check if config file exists
    if [ -f "$CLAUDE_CONFIG" ]; then
        echo "Existing config file found at: $CLAUDE_CONFIG"
        echo ""
        echo "The config file already exists. You have two options:"
        echo "  1. Merge the OpenCV MCP server into your existing config"
        echo "  2. Backup and replace the config file"
        echo ""
        read -p "Choose option (1=merge, 2=replace, 3=skip): " choice
        
        case $choice in
            1)
                echo "Merging configuration..."
                # Use Python to merge JSON
                python3 << EOF
import json
import sys

# Read existing config
with open("$CLAUDE_CONFIG", 'r') as f:
    existing = json.load(f)

# Read new config
with open("claude_desktop_config.json", 'r') as f:
    new = json.load(f)

# Merge mcpServers
if "mcpServers" not in existing:
    existing["mcpServers"] = {}
existing["mcpServers"].update(new["mcpServers"])

# Write back
with open("$CLAUDE_CONFIG", 'w') as f:
    json.dump(existing, f, indent=2)

print("✓ Configuration merged successfully")
EOF
                ;;
            2)
                echo "Backing up existing config..."
                cp "$CLAUDE_CONFIG" "${CLAUDE_CONFIG}.backup.$(date +%Y%m%d_%H%M%S)"
                cp claude_desktop_config.json "$CLAUDE_CONFIG"
                echo -e "${GREEN}✓ Config replaced (backup created)${NC}"
                ;;
            3)
                echo "Skipping Claude Desktop setup"
                ;;
            *)
                echo "Invalid choice, skipping"
                ;;
        esac
    else
        echo "Creating new config file..."
        cp claude_desktop_config.json "$CLAUDE_CONFIG"
        echo -e "${GREEN}✓ Config file created at: $CLAUDE_CONFIG${NC}"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Restart Claude Desktop (or Cursor)"
echo "  2. Verify the MCP server is connected"
echo "  3. Try using OpenCV tools!"
echo ""
echo "Configuration file location:"
if [ -n "$CLAUDE_CONFIG" ] && [ -f "$CLAUDE_CONFIG" ]; then
    echo "  $CLAUDE_CONFIG"
else
    echo "  See MCP_SETUP.md for manual setup instructions"
fi
echo ""
echo "Available tools: 22 OpenCV computer vision tools"
echo "  - Image processing (resize, crop, rotate, etc.)"
echo "  - Edge detection and contour analysis"
echo "  - Face and object detection"
echo "  - Video processing and analysis"
echo ""
echo "For more information, see: MCP_SETUP.md"
echo ""


