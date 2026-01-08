#!/usr/bin/env python3
"""
Test MCP server via docker exec to verify it works as an MCP server.

This script tests that the Docker container can run as an MCP server
and respond to MCP protocol requests.
"""

import asyncio
import json
import sys
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

async def test_docker_mcp_comprehensive():
    """Comprehensive test of MCP server in Docker."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: MCP Server via Docker Exec")
    print("="*70)
    
    try:
        # Create server parameters for Docker
        server_params = StdioServerParameters(
            command="docker",
            args=["run", "-i", "--rm", "opencv-mcp-server:latest"],
            env=None
        )
        
        print("Connecting to MCP server via: docker run -i --rm opencv-mcp-server:latest")
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # Test 1: List tools
                print("\n[Test 1] Listing available tools...")
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"   Found {len(tool_names)} tools")
                
                if len(tool_names) == 0:
                    test_results["failed"].append("No tools found")
                    print("   ✗ FAILED")
                    return
                
                test_results["passed"].append(f"List tools: {len(tool_names)} tools")
                print(f"   ✓ PASSED: {len(tool_names)} tools available")
                print(f"   Sample tools: {', '.join(tool_names[:5])}...")
                
                # Test 2: Get image stats from URL
                print("\n[Test 2] Testing get_image_stats_tool with URL...")
                image_urls = load_urls("image_urls.txt")
                if not image_urls:
                    test_results["skipped"].append("get_image_stats_tool: No URLs available")
                    print("   ⊘ SKIPPED: No URLs available")
                else:
                    test_url = image_urls[0]
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
                            result_data = json.loads(result.content[0].text) if result.content else {}
                            if "info" in result_data and "mean" in result_data:
                                test_results["passed"].append("get_image_stats_tool: Works correctly")
                                print(f"   ✓ PASSED: Stats calculated")
                                print(f"   Dimensions: {result_data['info']['width']}x{result_data['info']['height']}")
                                print(f"   Mean: {result_data['mean']:.2f}")
                            else:
                                test_results["failed"].append("get_image_stats_tool: Missing fields")
                                print(f"   ✗ FAILED: Missing required fields")
                    except Exception as e:
                        test_results["failed"].append(f"get_image_stats_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                
                # Test 3: Resize image from URL
                print("\n[Test 3] Testing resize_image_tool with URL...")
                if image_urls:
                    try:
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
                                # Check if it's a local path (not URL)
                                if output_path.startswith("http"):
                                    test_results["failed"].append("resize_image_tool: Output is URL, not local file")
                                    print(f"   ✗ FAILED: Output is URL")
                                else:
                                    # Verify dimensions
                                    if result_data["info"]["width"] == 300 and result_data["info"]["height"] == 200:
                                        test_results["passed"].append("resize_image_tool: Works correctly")
                                        print(f"   ✓ PASSED: Image resized correctly")
                                        print(f"   Output: {output_path[:60]}...")
                                        print(f"   Dimensions: {result_data['info']['width']}x{result_data['info']['height']}")
                                    else:
                                        test_results["failed"].append(f"resize_image_tool: Wrong dimensions")
                                        print(f"   ✗ FAILED: Wrong dimensions")
                            else:
                                test_results["failed"].append("resize_image_tool: Missing fields")
                                print(f"   ✗ FAILED: Missing required fields")
                    except Exception as e:
                        test_results["failed"].append(f"resize_image_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                
                # Test 4: Edge detection from URL
                print("\n[Test 4] Testing detect_edges_tool with URL...")
                if image_urls:
                    try:
                        result = await session.call_tool(
                            "detect_edges_tool",
                            arguments={
                                "image_path": test_url,
                                "method": "canny",
                                "threshold1": 100,
                                "threshold2": 200
                            }
                        )
                        
                        if result.isError:
                            test_results["failed"].append(f"detect_edges_tool error: {result.content}")
                            print(f"   ✗ FAILED: {result.content}")
                        else:
                            result_data = json.loads(result.content[0].text) if result.content else {}
                            if "path" in result_data:
                                output_path = result_data["path"]
                                if not output_path.startswith("http"):
                                    test_results["passed"].append("detect_edges_tool: Works correctly")
                                    print(f"   ✓ PASSED: Edge detection completed")
                                    print(f"   Output: {output_path[:60]}...")
                                else:
                                    test_results["failed"].append("detect_edges_tool: Output is URL")
                                    print(f"   ✗ FAILED: Output is URL")
                            else:
                                test_results["failed"].append("detect_edges_tool: Missing path")
                                print(f"   ✗ FAILED: Missing path")
                    except Exception as e:
                        test_results["failed"].append(f"detect_edges_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                
                # Test 5: Face detection from URL
                print("\n[Test 5] Testing detect_faces_tool with URL...")
                if image_urls:
                    try:
                        result = await session.call_tool(
                            "detect_faces_tool",
                            arguments={
                                "image_path": test_url,
                                "method": "haar",
                                "min_neighbors": 5
                            }
                        )
                        
                        if result.isError:
                            test_results["failed"].append(f"detect_faces_tool error: {result.content}")
                            print(f"   ✗ FAILED: {result.content}")
                        else:
                            result_data = json.loads(result.content[0].text) if result.content else {}
                            if "path" in result_data and "face_count" in result_data:
                                face_count = result_data["face_count"]
                                test_results["passed"].append(f"detect_faces_tool: Found {face_count} faces")
                                print(f"   ✓ PASSED: Face detection completed")
                                print(f"   Faces found: {face_count}")
                                print(f"   Output: {result_data['path'][:60]}...")
                            else:
                                test_results["failed"].append("detect_faces_tool: Missing fields")
                                print(f"   ✗ FAILED: Missing required fields")
                    except Exception as e:
                        test_results["failed"].append(f"detect_faces_tool exception: {str(e)}")
                        print(f"   ✗ ERROR: {str(e)}")
                
    except Exception as e:
        test_results["failed"].append(f"Docker MCP test error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def print_summary():
    """Print test summary."""
    print("\n" + "="*70)
    print("DOCKER MCP EXEC TEST SUMMARY")
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
    results_file = Path(__file__).parent / "test_mcp_docker_exec_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

async def main():
    """Run Docker MCP exec tests."""
    print("="*70)
    print("OpenCV MCP Server - Docker Exec MCP Tests")
    print("="*70)
    print("Testing MCP server via docker exec")
    print("="*70)
    
    await test_docker_mcp_comprehensive()
    
    print_summary()
    
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(main())


