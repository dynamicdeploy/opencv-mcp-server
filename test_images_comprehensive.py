#!/usr/bin/env python3
"""
Comprehensive test script for testing OpenCV MCP Server with both local and online images.
Tests multiple tools on various image sources.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

try:
    from mcp.client.stdio import StdioServerParameters, stdio_client
    from mcp.client.session import ClientSession
except ImportError:
    print("ERROR: MCP client not available. Install with: pip install mcp")
    sys.exit(1)

# Test configuration
DOCKER_IMAGE = "hackerdogs/opencv-mcp-server:latest"
USE_DOCKER = True  # Set to False to test locally

test_results = {
    "passed": [],
    "failed": [],
    "skipped": [],
    "details": {}
}

def load_urls(filename: str) -> List[str]:
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

def get_local_images() -> List[str]:
    """Get local images from the public folder.
    When using Docker, paths are mounted at /app/public/"""
    local_images = []
    public_dir = Path(__file__).parent / "public"
    if public_dir.exists():
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif']:
            found_images = list(public_dir.glob(ext))
            if USE_DOCKER:
                # Convert to Docker container paths
                for img in found_images:
                    # Map to /app/public/filename
                    docker_path = f"/app/public/{img.name}"
                    local_images.append(docker_path)
            else:
                # Use local paths
                local_images.extend([str(img) for img in found_images])
    return local_images

async def test_tool(session: ClientSession, tool_name: str, arguments: Dict[str, Any], test_name: str) -> bool:
    """Test a single tool and return True if successful."""
    try:
        print(f"  Testing {tool_name}...")
        result = await session.call_tool(tool_name, arguments=arguments)
        
        if result.isError:
            error_msg = str(result.content) if result.content else "Unknown error"
            test_results["failed"].append(f"{test_name}: {error_msg}")
            print(f"    ✗ FAILED: {error_msg[:100]}")
            return False
        
        # Parse result
        if result.content:
            result_text = result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
            try:
                result_data = json.loads(result_text)
                test_results["passed"].append(f"{test_name}: {tool_name}")
                print(f"    ✓ PASSED")
                
                # Print key info
                if "info" in result_data:
                    info = result_data["info"]
                    if "width" in info and "height" in info:
                        print(f"      Dimensions: {info['width']}x{info['height']}")
                if "path" in result_data:
                    path = result_data["path"]
                    print(f"      Output: {path[:60]}{'...' if len(path) > 60 else ''}")
                if "objects" in result_data:
                    count = len(result_data["objects"])
                    print(f"      Objects detected: {count}")
                if "faces" in result_data:
                    count = len(result_data["faces"])
                    print(f"      Faces detected: {count}")
                
                return True
            except json.JSONDecodeError:
                # Result might not be JSON
                test_results["passed"].append(f"{test_name}: {tool_name}")
                print(f"    ✓ PASSED (non-JSON result)")
                return True
        else:
            test_results["failed"].append(f"{test_name}: No result content")
            print(f"    ✗ FAILED: No result content")
            return False
            
    except Exception as e:
        test_results["failed"].append(f"{test_name}: Exception - {str(e)}")
        print(f"    ✗ ERROR: {str(e)}")
        return False

async def test_image_sources(session: ClientSession):
    """Test various tools on different image sources."""
    
    # Get test images
    local_images = get_local_images()
    online_urls = load_urls("image_urls.txt")
    
    print(f"\n📁 Local images found: {len(local_images)}")
    print(f"🌐 Online URLs found: {len(online_urls)}")
    
    # Combine all test images (prioritize online for now, add local if needed)
    test_images = online_urls[:3]  # Test first 3 online images
    if local_images:
        test_images.extend(local_images[:2])  # Add 2 local images
    
    print(f"\n🧪 Testing {len(test_images)} images...")
    
    for idx, image_path in enumerate(test_images, 1):
        is_url = image_path.startswith("http")
        image_type = "URL" if is_url else "Local"
        print(f"\n{'='*70}")
        print(f"Image {idx}/{len(test_images)}: {image_type}")
        print(f"{'='*70}")
        print(f"Path: {image_path[:80]}{'...' if len(image_path) > 80 else ''}")
        
        # Test 1: Get Image Stats
        await test_tool(
            session,
            "get_image_stats_tool",
            {"image_path": image_path, "channels": True},
            f"Image {idx} - Stats"
        )
        
        # Test 2: Resize Image
        await test_tool(
            session,
            "resize_image_tool",
            {"image_path": image_path, "width": 300, "height": 200},
            f"Image {idx} - Resize"
        )
        
        # Test 3: Edge Detection
        await test_tool(
            session,
            "detect_edges_tool",
            {"image_path": image_path, "method": "canny", "threshold1": 100, "threshold2": 200},
            f"Image {idx} - Edge Detection"
        )
        
        # Test 4: Face Detection (only for photos)
        if is_url or "face" in image_path.lower() or "people" in image_path.lower() or "person" in image_path.lower():
            await test_tool(
                session,
                "detect_faces_tool",
                {"image_path": image_path, "method": "haar"},
                f"Image {idx} - Face Detection"
            )
        
        # Test 5: Object Detection (YOLO) - only for URLs and larger images
        if is_url:
            await test_tool(
                session,
                "detect_objects_tool",
                {"image_path": image_path, "confidence_threshold": 0.5},
                f"Image {idx} - Object Detection"
            )
        
        # Test 6: Histogram (skip if tool doesn't exist)
        # Note: Histogram tool may have a different name or may not be available

async def main():
    """Main test function."""
    print("="*70)
    print("OpenCV MCP Server - Comprehensive Image Testing")
    print("="*70)
    print(f"Using: {'Docker' if USE_DOCKER else 'Local'} execution")
    print(f"Docker image: {DOCKER_IMAGE}")
    print("="*70)
    
    # Setup server parameters
    if USE_DOCKER:
        # Mount the public directory and current directory for local image access
        public_dir = Path(__file__).parent / "public"
        current_dir = Path(__file__).parent
        
        docker_args = ["run", "-i", "--rm"]
        
        # Mount public directory if it exists (read-only for input)
        if public_dir.exists():
            docker_args.extend(["-v", f"{public_dir}:/app/public:ro"])
        
        # Mount current directory for output files (writable)
        docker_args.extend(["-v", f"{current_dir}:/app/output"])
        docker_args.append(DOCKER_IMAGE)
        
        server_params = StdioServerParameters(
            command="docker",
            args=docker_args
        )
    else:
        python_exe = sys.executable
        server_params = StdioServerParameters(
            command=python_exe,
            args=["-m", "opencv_mcp_server.main"],
            env=None
        )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                await session.initialize()
                
                # List tools
                print("\n📋 Listing available tools...")
                tools = await session.list_tools()
                tool_names = [tool.name for tool in tools.tools]
                print(f"   Found {len(tool_names)} tools")
                test_results["passed"].append(f"Tools available: {len(tool_names)}")
                
                # Test images
                await test_image_sources(session)
                
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        test_results["failed"].append(f"Fatal error: {str(e)}")
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⏭️  Skipped: {len(test_results['skipped'])}")
    
    if test_results["failed"]:
        print("\n❌ Failures:")
        for failure in test_results["failed"][:10]:  # Show first 10
            print(f"   - {failure}")
        if len(test_results["failed"]) > 10:
            print(f"   ... and {len(test_results['failed']) - 10} more")
    
    # Save results
    results_file = Path(__file__).parent / "test_images_comprehensive_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\n💾 Results saved to: {results_file}")
    
    # Exit code
    exit_code = 0 if len(test_results["failed"]) == 0 else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    asyncio.run(main())
