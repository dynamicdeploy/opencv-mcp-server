#!/usr/bin/env python3
"""
Test Docker Hub image by pulling and verifying functionality.

This script tests the image as if it were downloaded from Docker Hub.
"""

import asyncio
import json
import sys
import subprocess
from pathlib import Path

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("ERROR: MCP client not available. Install with: pip install mcp")
    sys.exit(1)

test_results = {
    "passed": [],
    "failed": [],
    "skipped": []
}

def load_urls(filename):
    """Load URLs from a text file."""
    urls = []
    filepath = Path(__file__).parent / filename
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    return urls

def test_docker_image_exists(image_name):
    """Check if Docker image exists locally."""
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", image_name],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception:
        return False

def test_pull_from_dockerhub(dockerhub_username):
    """Test pulling image from Docker Hub."""
    print("\n" + "="*70)
    print("TEST: Pull Image from Docker Hub")
    print("="*70)
    
    image_name = f"{dockerhub_username}/opencv-mcp-server:latest"
    
    print(f"Pulling: {image_name}")
    try:
        result = subprocess.run(
            ["docker", "pull", image_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            test_results["passed"].append(f"Pulled image from Docker Hub: {image_name}")
            print(f"✓ Successfully pulled image from Docker Hub")
            return image_name
        else:
            test_results["failed"].append(f"Failed to pull image: {result.stderr}")
            print(f"✗ Failed to pull image: {result.stderr}")
            return None
    except Exception as e:
        test_results["failed"].append(f"Error pulling image: {str(e)}")
        print(f"✗ Error: {str(e)}")
        return None

async def test_image_functionality(image_name):
    """Test image functionality via MCP."""
    print("\n" + "="*70)
    print("TEST: Image Functionality via MCP")
    print("="*70)
    
    try:
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "-i", "--rm", image_name],
            env=None
        )
        
        print(f"Connecting to: docker run -i --rm {image_name}")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: List tools
                print("\n[Test 1] Listing tools...")
                tools = await session.list_tools()
                tool_count = len(tools.tools)
                print(f"   Found {tool_count} tools")
                
                if tool_count == 0:
                    test_results["failed"].append("No tools found")
                    return
                
                test_results["passed"].append(f"List tools: {tool_count} tools")
                print(f"   ✓ PASSED: {tool_count} tools available")
                
                # Test 2: Process image from URL
                print("\n[Test 2] Testing image processing from URL...")
                image_urls = load_urls("image_urls.txt")
                if not image_urls:
                    test_results["skipped"].append("Image processing: No URLs available")
                    print("   ⊘ SKIPPED: No URLs available")
                else:
                    test_url = image_urls[0]
                    print(f"   URL: {test_url[:60]}...")
                    
                    # Test get_image_stats_tool
                    result = await session.call_tool(
                        "get_image_stats_tool",
                        arguments={
                            "image_path": test_url,
                            "channels": True
                        }
                    )
                    
                    if result.isError:
                        test_results["failed"].append(f"get_image_stats_tool error: {result.content}")
                        print(f"   ✗ FAILED: {result.content}")
                    else:
                        result_data = json.loads(result.content[0].text) if result.content else {}
                        if "info" in result_data:
                            test_results["passed"].append("get_image_stats_tool: Works")
                            print(f"   ✓ PASSED: Stats calculated")
                            print(f"   Dimensions: {result_data['info']['width']}x{result_data['info']['height']}")
                        else:
                            test_results["failed"].append("get_image_stats_tool: Missing info")
                            print(f"   ✗ FAILED: Missing info")
                    
                    # Test resize_image_tool
                    print("\n[Test 3] Testing resize_image_tool...")
                    result = await session.call_tool(
                        "resize_image_tool",
                        arguments={
                            "image_path": test_url,
                            "width": 300,
                            "height": 200
                        }
                    )
                    
                    if result.isError:
                        test_results["failed"].append(f"resize_image_tool error: {result.content}")
                        print(f"   ✗ FAILED: {result.content}")
                    else:
                        result_data = json.loads(result.content[0].text) if result.content else {}
                        if "path" in result_data and "info" in result_data:
                            output_path = result_data["path"]
                            if output_path.startswith("http"):
                                test_results["failed"].append("resize_image_tool: Output is URL")
                                print(f"   ✗ FAILED: Output is URL")
                            else:
                                if result_data["info"]["width"] == 300 and result_data["info"]["height"] == 200:
                                    test_results["passed"].append("resize_image_tool: Works correctly")
                                    print(f"   ✓ PASSED: Resized correctly to 300x200")
                                    print(f"   Output: {output_path[:60]}...")
                                else:
                                    test_results["failed"].append("resize_image_tool: Wrong dimensions")
                                    print(f"   ✗ FAILED: Wrong dimensions")
                        else:
                            test_results["failed"].append("resize_image_tool: Missing fields")
                            print(f"   ✗ FAILED: Missing fields")
                
    except Exception as e:
        test_results["failed"].append(f"MCP test error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def print_summary():
    """Print test summary."""
    print("\n" + "="*70)
    print("DOCKER HUB IMAGE TEST SUMMARY")
    print("="*70)
    print(f"Passed: {len(test_results['passed'])}")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Skipped: {len(test_results['skipped'])}")
    
    if test_results['passed']:
        print("\n✓ Passed Tests:")
        for test in test_results['passed']:
            print(f"  ✓ {test}")
    
    if test_results['failed']:
        print("\n✗ Failed Tests:")
        for test in test_results['failed']:
            print(f"  ✗ {test}")
    
    if test_results['skipped']:
        print("\n⊘ Skipped Tests:")
        for test in test_results['skipped']:
            print(f"  ⊘ {test}")
    
    # Save results
    results_file = Path(__file__).parent / "test_dockerhub_pull_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

async def main():
    """Run Docker Hub pull tests."""
    print("="*70)
    print("OpenCV MCP Server - Docker Hub Pull Test")
    print("="*70)
    
    # Get Docker Hub username from command line or environment
    dockerhub_username = sys.argv[1] if len(sys.argv) > 1 else None
    
    if not dockerhub_username:
        dockerhub_username = input("Enter Docker Hub username (or 'local' to test local image): ").strip()
    
    if dockerhub_username.lower() == 'local':
        image_name = "opencv-mcp-server:latest"
        print(f"\nTesting local image: {image_name}")
        if not test_docker_image_exists(image_name):
            print("Local image not found. Please build it first: docker build -t opencv-mcp-server:latest .")
            sys.exit(1)
    else:
        # Pull from Docker Hub
        image_name = test_pull_from_dockerhub(dockerhub_username)
        if not image_name:
            print("\nFailed to pull image. Testing with local image instead...")
            image_name = "opencv-mcp-server:latest"
            if not test_docker_image_exists(image_name):
                print("Local image also not found. Exiting.")
                sys.exit(1)
    
    # Test functionality
    await test_image_functionality(image_name)
    
    # Print summary
    print_summary()
    
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())

