#!/usr/bin/env python3
"""
Test MCP server using MCP client.

This script tests the OpenCV MCP server using the MCP client library
to verify that the server works correctly via the MCP protocol.
"""

import asyncio
import json
import sys
import subprocess
import os
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

async def test_mcp_server_local():
    """Test MCP server running locally."""
    print("\n" + "="*70)
    print("TEST: MCP Server (Local Execution)")
    print("="*70)
    
    try:
        # Get the Python executable and module path
        python_exe = sys.executable
        server_script = str(Path(__file__).parent / "opencv_mcp_server" / "main.py")
        
        # Create server parameters
        server_params = StdioServerParameters(
            command=python_exe,
            args=["-m", "opencv_mcp_server.main"],
            env=None
        )
        
        print(f"Starting MCP server: {python_exe} -m opencv_mcp_server.main")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                print("\n1. Listing available tools...")
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"   Found {len(tool_names)} tools")
                
                if len(tool_names) == 0:
                    test_results["failed"].append("No tools found in MCP server")
                    print("   ✗ FAILED: No tools available")
                    return
                
                test_results["passed"].append(f"MCP server local: {len(tool_names)} tools available")
                print(f"   ✓ PASSED: {len(tool_names)} tools available")
                
                # Test a simple tool call - get_image_stats_tool
                print("\n2. Testing get_image_stats_tool with URL...")
                image_urls = load_urls("image_urls.txt")
                if image_urls:
                    test_url = image_urls[0]
                    print(f"   URL: {test_url[:60]}...")
                    
                    try:
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
                            # Parse the result
                            result_data = json.loads(result.content[0].text) if result.content else {}
                            if "info" in result_data:
                                test_results["passed"].append("MCP server local: get_image_stats_tool works")
                                print(f"   ✓ PASSED: Tool executed successfully")
                                print(f"   Dimensions: {result_data['info'].get('width', 'N/A')}x{result_data['info'].get('height', 'N/A')}")
                            else:
                                test_results["failed"].append("get_image_stats_tool: Missing 'info' in result")
                                print(f"   ✗ FAILED: Missing 'info' in result")
                    except Exception as e:
                        test_results["failed"].append(f"get_image_stats_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
                # Test resize_image_tool
                print("\n3. Testing resize_image_tool with URL...")
                if image_urls:
                    try:
                        result = await session.call_tool(
                            "resize_image_tool",
                            arguments={
                                "image_path": test_url,
                                "width": 200,
                                "height": 150
                            }
                        )
                        
                        if result.isError:
                            test_results["failed"].append(f"resize_image_tool error: {result.content}")
                            print(f"   ✗ FAILED: {result.content}")
                        else:
                            result_data = json.loads(result.content[0].text) if result.content else {}
                            if "path" in result_data and "info" in result_data:
                                # Verify output path is not a URL
                                output_path = result_data["path"]
                                if output_path.startswith("http"):
                                    test_results["failed"].append("resize_image_tool: Output path is URL, not local file")
                                    print(f"   ✗ FAILED: Output path is URL: {output_path[:60]}...")
                                else:
                                    test_results["passed"].append("MCP server local: resize_image_tool works")
                                    print(f"   ✓ PASSED: Tool executed successfully")
                                    print(f"   Output: {output_path[:60]}...")
                                    print(f"   Dimensions: {result_data['info'].get('width', 'N/A')}x{result_data['info'].get('height', 'N/A')}")
                            else:
                                test_results["failed"].append("resize_image_tool: Missing 'path' or 'info' in result")
                                print(f"   ✗ FAILED: Missing required fields in result")
                    except Exception as e:
                        test_results["failed"].append(f"resize_image_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
    except Exception as e:
        test_results["failed"].append(f"MCP server local error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_mcp_server_docker():
    """Test MCP server running in Docker."""
    print("\n" + "="*70)
    print("TEST: MCP Server (Docker Execution)")
    print("="*70)
    
    # Check if Docker image exists
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", "opencv-mcp-server:latest"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("✗ Docker image 'opencv-mcp-server:latest' not found")
            print("  Build it first with: docker build -t opencv-mcp-server:latest .")
            test_results["skipped"].append("Docker MCP test: Image not found")
            return
    except FileNotFoundError:
        print("✗ Docker not found")
        test_results["skipped"].append("Docker MCP test: Docker not installed")
        return
    
    try:
        # Create server parameters for Docker
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "-i", "--rm", "opencv-mcp-server:latest"],
            env=None
        )
        
        print("Starting MCP server via Docker: docker run -i --rm opencv-mcp-server:latest")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                print("\n1. Listing available tools...")
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"   Found {len(tool_names)} tools")
                
                if len(tool_names) == 0:
                    test_results["failed"].append("Docker: No tools found in MCP server")
                    print("   ✗ FAILED: No tools available")
                    return
                
                test_results["passed"].append(f"MCP server Docker: {len(tool_names)} tools available")
                print(f"   ✓ PASSED: {len(tool_names)} tools available")
                
                # Test a tool call
                print("\n2. Testing get_image_stats_tool with URL...")
                image_urls = load_urls("image_urls.txt")
                if image_urls:
                    test_url = image_urls[0]
                    print(f"   URL: {test_url[:60]}...")
                    
                    try:
                        result = await session.call_tool(
                            "get_image_stats_tool",
                            arguments={
                                "image_path": test_url,
                                "channels": True
                            }
                        )
                        
                        if result.isError:
                            test_results["failed"].append(f"Docker get_image_stats_tool error: {result.content}")
                            print(f"   ✗ FAILED: {result.content}")
                        else:
                            result_data = json.loads(result.content[0].text) if result.content else {}
                            if "info" in result_data:
                                test_results["passed"].append("MCP server Docker: get_image_stats_tool works")
                                print(f"   ✓ PASSED: Tool executed successfully")
                                print(f"   Dimensions: {result_data['info'].get('width', 'N/A')}x{result_data['info'].get('height', 'N/A')}")
                            else:
                                test_results["failed"].append("Docker get_image_stats_tool: Missing 'info' in result")
                                print(f"   ✗ FAILED: Missing 'info' in result")
                    except Exception as e:
                        test_results["failed"].append(f"Docker get_image_stats_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                        import traceback
                        traceback.print_exc()
                
    except Exception as e:
        test_results["failed"].append(f"MCP server Docker error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def print_summary():
    """Print test summary."""
    print("\n" + "="*70)
    print("MCP CLIENT TEST SUMMARY")
    print("="*70)
    print(f"Passed: {len(test_results['passed'])}")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Skipped: {len(test_results['skipped'])}")
    print(f"Total: {len(test_results['passed']) + len(test_results['failed']) + len(test_results['skipped'])}")
    
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
    results_file = Path(__file__).parent / "test_mcp_client_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

async def main():
    """Run all MCP client tests."""
    print("="*70)
    print("OpenCV MCP Server - MCP Client Tests")
    print("="*70)
    print("Testing MCP protocol communication")
    print("="*70)
    
    # Test local server
    await test_mcp_server_local()
    
    # Test Docker server
    await test_mcp_server_docker()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())


