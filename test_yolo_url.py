#!/usr/bin/env python3
"""
Test YOLO object detection with URL image
"""
import asyncio
import json
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.session import ClientSession

async def test_yolo_url():
    """Test YOLO object detection with a URL image"""
    
    # Use an image URL that likely contains objects
    test_url = "https://media.istockphoto.com/id/1480574526/photo/happy-multigenerational-people-having-fun-sitting-on-grass-in-a-public-park.jpg?s=612x612&w=0&k=20&c=iIzSiY2FK9mWTCmV8Ip8zpvXma7f1Qbd-UuKXNJodPg="
    
    server_params = StdioServerParameters(
        command="docker",
        args=["run", "-i", "--rm", "opencv-mcp-server:0.1.6"]
    )
    
    print("=== Testing YOLO Object Detection with URL ===")
    print(f"Image URL: {test_url}")
    print()
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List tools
            tools = await session.list_tools()
            detect_objects_tool = None
            for tool in tools.tools:
                if tool.name == "detect_objects_tool":
                    detect_objects_tool = tool
                    break
            
            if not detect_objects_tool:
                print("❌ detect_objects_tool not found")
                return
            
            print(f"✅ Found tool: {detect_objects_tool.name}")
            print(f"   Description: {detect_objects_tool.description[:100]}...")
            print()
            
            # Call detect_objects_tool with URL
            print("Calling detect_objects_tool with URL...")
            result = await session.call_tool(
                "detect_objects_tool",
                arguments={
                    "image_path": test_url,
                    "confidence_threshold": 0.5,
                    "draw": True
                }
            )
            
            print("✅ Tool call completed")
            print()
            
            # Parse result
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        try:
                            data = json.loads(content.text)
                            
                            # Check for errors
                            if "error" in data:
                                print(f"❌ Error: {data['error']}")
                                if "download_instructions" in data:
                                    print(f"   Instructions: {data['download_instructions'][:200]}...")
                                return
                            
                            # Check for success
                            if "object_count" in data:
                                print(f"✅ Object detection successful!")
                                print(f"   Objects detected: {data['object_count']}")
                                
                                if "objects" in data and len(data['objects']) > 0:
                                    print(f"   First few objects:")
                                    for obj in data['objects'][:5]:
                                        print(f"     - {obj.get('class_name', 'unknown')}: {obj.get('confidence', 0):.2f} confidence")
                                
                                if "image_base64" in data:
                                    print(f"   ✅ Image with detections returned (base64)")
                                    print(f"   Base64 length: {len(data['image_base64'])} characters")
                                else:
                                    print(f"   ⚠️  No image_base64 in response")
                                
                                if "model_info" in data:
                                    print(f"   Model info: {data['model_info']}")
                            else:
                                print(f"⚠️  Unexpected response format: {list(data.keys())}")
                                
                        except json.JSONDecodeError as e:
                            print(f"❌ Failed to parse JSON: {e}")
                            print(f"   Response: {content.text[:200]}...")
                    else:
                        print(f"⚠️  Unexpected content type: {type(content)}")
            else:
                print("❌ No content in response")

if __name__ == "__main__":
    asyncio.run(test_yolo_url())

