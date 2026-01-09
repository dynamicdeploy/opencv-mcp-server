#!/usr/bin/env python3
"""
Test script to verify the color space conversion fix.
Tests the specific RGB to HSV conversion that was failing.
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

def create_test_image():
    """Create a simple test image."""
    # Create a 100x100 RGB test image with some color
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    img[:, :, 0] = 255  # Red channel
    img[:, :, 1] = 128  # Green channel
    img[:, :, 2] = 64   # Blue channel
    return img

def save_test_image(img, path):
    """Save test image to file."""
    cv2.imwrite(str(path), img)
    return path

def test_color_space_conversion(source_space, target_space, description):
    """Test a color space conversion."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"Conversion: {source_space} -> {target_space}")
    print(f"{'='*60}")
    
    try:
        # Create test image
        test_img = create_test_image()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            tmp_path = tmp.name
            cv2.imwrite(tmp_path, test_img)
        
        try:
            # Test the conversion
            result = convert_color_space_tool(
                image_path=tmp_path,
                source_space=source_space,
                target_space=target_space
            )
            
            # Verify result structure
            assert 'source_space' in result, "Missing source_space in result"
            assert 'target_space' in result, "Missing target_space in result"
            assert 'info' in result, "Missing info in result"
            assert 'path' in result, "Missing path in result"
            assert 'image_base64' in result, "Missing image_base64 in result"
            
            # Verify values
            assert result['source_space'] == source_space, f"Source space mismatch: {result['source_space']} != {source_space}"
            assert result['target_space'] == target_space, f"Target space mismatch: {result['target_space']} != {target_space}"
            
            # Verify image info (check for actual keys returned by get_image_info)
            assert 'channels' in result['info'], "Missing channels in info"
            assert 'width' in result['info'], "Missing width in info"
            assert 'height' in result['info'], "Missing height in info"
            
            # Verify base64 encoding
            assert result['image_base64'].startswith('data:image/'), "Invalid base64 format"
            
            print(f"✅ PASSED: {description}")
            print(f"   - Dimensions: {result['info'].get('width', 'N/A')}x{result['info'].get('height', 'N/A')}")
            print(f"   - Channels: {result['info'].get('channels', 'N/A')}")
            print(f"   - Output path: {result['path']}")
            
            return True
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            if 'result' in locals() and os.path.exists(result.get('path', '')):
                try:
                    os.unlink(result['path'])
                except:
                    pass
                    
    except Exception as e:
        print(f"❌ FAILED: {description}")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all color space conversion tests."""
    print("="*60)
    print("Color Space Conversion Fix Test Suite")
    print("="*60)
    
    tests = [
        # The specific failing case
        ("RGB", "HSV", "RGB to HSV (the original failing case)"),
        
        # Other common conversions
        ("RGB", "BGR", "RGB to BGR"),
        ("BGR", "RGB", "BGR to RGB"),
        ("BGR", "HSV", "BGR to HSV"),
        ("HSV", "RGB", "HSV to RGB"),
        ("HSV", "BGR", "HSV to BGR"),
        ("RGB", "GRAY", "RGB to GRAY"),
        ("BGR", "GRAY", "BGR to GRAY"),
        ("GRAY", "BGR", "GRAY to BGR"),
        ("RGB", "LAB", "RGB to LAB"),
        ("LAB", "RGB", "LAB to RGB"),
        
        # Edge cases
        ("BGR", "BGR", "BGR to BGR (identity)"),
    ]
    
    passed = 0
    failed = 0
    
    for source, target, desc in tests:
        if test_color_space_conversion(source, target, desc):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*60)
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

