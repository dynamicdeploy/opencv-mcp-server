#!/usr/bin/env python3
"""
Test color space conversion with the specific image that was failing.
"""

import sys
import os
from pathlib import Path

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from opencv_mcp_server.image_basics import convert_color_space_tool

def test_image_url(url, source_space, target_space):
    """Test color space conversion with a specific image URL."""
    print(f"\n{'='*70}")
    print(f"Testing: {source_space} -> {target_space}")
    print(f"Image URL: {url}")
    print(f"{'='*70}")
    
    try:
        result = convert_color_space_tool(
            image_path=url,
            source_space=source_space,
            target_space=target_space
        )
        
        # Verify result structure
        assert 'source_space' in result, "Missing source_space"
        assert 'target_space' in result, "Missing target_space"
        assert 'info' in result, "Missing info"
        assert 'path' in result, "Missing path"
        assert 'image_base64' in result, "Missing image_base64"
        
        # Verify values
        assert result['source_space'] == source_space
        assert result['target_space'] == target_space
        
        # Verify no COLOR_BGR2BGR errors
        result_str = str(result)
        if 'COLOR_BGR2BGR' in result_str:
            print(f"❌ FAILED: Still contains COLOR_BGR2BGR reference!")
            return False
        
        print(f"✅ SUCCESS: Conversion completed")
        print(f"   - Source: {result['source_space']}")
        print(f"   - Target: {result['target_space']}")
        print(f"   - Dimensions: {result['info'].get('width', 'N/A')}x{result['info'].get('height', 'N/A')}")
        print(f"   - Channels: {result['info'].get('channels', 'N/A')}")
        print(f"   - Output path: {result['path']}")
        print(f"   - Base64 length: {len(result['image_base64'])} chars")
        
        # Clean up output file
        if os.path.exists(result.get('path', '')):
            try:
                os.unlink(result['path'])
            except:
                pass
        
        return True
        
    except AttributeError as e:
        if "COLOR_BGR2BGR" in str(e):
            print(f"❌ FAILED: COLOR_BGR2BGR error still present!")
            print(f"   Error: {e}")
            return False
        else:
            print(f"❌ FAILED: AttributeError: {e}")
            return False
    except Exception as e:
        if "COLOR_BGR2BGR" in str(e):
            print(f"❌ FAILED: COLOR_BGR2BGR error in exception!")
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            return False
        else:
            print(f"❌ FAILED: Unexpected error: {e}")
            print(f"   Error type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Test the specific image URL that was failing."""
    image_url = "https://media.npr.org/assets/img/2014/10/09/mcream_wide-e59974dc0d96661f6cb9f647e2f0dcde3401f6cc.jpg?s=800&c=85&f=webp"
    
    print("="*70)
    print("Testing Color Space Conversion with Specific Image URL")
    print("="*70)
    print(f"\nImage URL: {image_url}")
    
    # Test the original failing case
    test_cases = [
        ("RGB", "HSV", "Original failing case"),
        ("RGB", "BGR", "RGB to BGR"),
        ("BGR", "HSV", "BGR to HSV"),
        ("BGR", "RGB", "BGR to RGB"),
        ("BGR", "GRAY", "BGR to GRAY"),
        ("RGB", "LAB", "RGB to LAB"),
    ]
    
    passed = 0
    failed = 0
    
    for source, target, description in test_cases:
        print(f"\n[{description}]")
        if test_image_url(image_url, source, target):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("="*70)
    
    if failed == 0:
        print("\n✅ All tests passed! The fix is working correctly.")
    else:
        print(f"\n❌ {failed} test(s) failed. Please review the errors above.")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

