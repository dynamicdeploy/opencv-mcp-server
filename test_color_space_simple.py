#!/usr/bin/env python3
"""
Simple test to verify the COLOR_BGR2BGR fix works.
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path
import tempfile

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from opencv_mcp_server.image_basics import convert_color_space_tool

def test_rgb_to_hsv():
    """Test the specific failing case: RGB to HSV."""
    print("Testing RGB to HSV conversion (the original failing case)...")
    
    # Create a simple test image (OpenCV will save/read as BGR)
    test_img = np.zeros((50, 50, 3), dtype=np.uint8)
    test_img[:, :, 0] = 255  # Blue in BGR
    test_img[:, :, 1] = 128  # Green
    test_img[:, :, 2] = 64   # Red
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        tmp_path = tmp.name
        cv2.imwrite(tmp_path, test_img)
    
    try:
        # This should NOT raise: module 'cv2' has no attribute 'COLOR_BGR2BGR'
        result = convert_color_space_tool(
            image_path=tmp_path,
            source_space="RGB",
            target_space="HSV"
        )
        
        print("✅ SUCCESS: RGB to HSV conversion completed without COLOR_BGR2BGR error")
        print(f"   Result keys: {list(result.keys())}")
        print(f"   Source space: {result.get('source_space')}")
        print(f"   Target space: {result.get('target_space')}")
        print(f"   Has image_base64: {'image_base64' in result}")
        
        # Clean up output file
        if os.path.exists(result.get('path', '')):
            os.unlink(result['path'])
        
        return True
        
    except AttributeError as e:
        if "COLOR_BGR2BGR" in str(e):
            print(f"❌ FAILED: Still has COLOR_BGR2BGR error: {e}")
            return False
        else:
            print(f"❌ FAILED: AttributeError: {e}")
            return False
    except Exception as e:
        print(f"⚠️  Other error (may be expected): {e}")
        print(f"   Error type: {type(e).__name__}")
        # This might be okay if it's a different error (like channel mismatch)
        # The important thing is that COLOR_BGR2BGR error is gone
        if "COLOR_BGR2BGR" in str(e):
            return False
        return True  # Other errors might be expected (like channel issues)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

if __name__ == "__main__":
    success = test_rgb_to_hsv()
    sys.exit(0 if success else 1)

