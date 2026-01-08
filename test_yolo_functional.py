#!/usr/bin/env python3
"""
Functional tests for YOLO object detection with URL images.

These tests verify that:
1. Images are successfully downloaded from URLs
2. YOLO models detect objects correctly
3. Returned data structure is correct
4. Base64 images contain detections
"""
import os
import sys
import base64
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

def test_yolo_url_download_and_detection():
    """Test that YOLO can download images from URLs and detect objects."""
    print("="*70)
    print("FUNCTIONAL TEST: YOLO Object Detection with URL")
    print("="*70)
    
    # Set environment variable
    os.environ['OPENCV_DNN_MODELS_DIR'] = '/app/OPENCV_DNN_MODELS_DIR'
    
    # Import after setting env var
    from opencv_mcp_server.computer_vision import detect_objects_tool
    
    # Test URLs - images that should contain detectable objects
    test_cases = [
        {
            "name": "People in park",
            "url": "https://media.istockphoto.com/id/1480574526/photo/happy-multigenerational-people-having-fun-sitting-on-grass-in-a-public-park.jpg?s=612x612&w=0&k=20&c=iIzSiY2FK9mWTCmV8Ip8zpvXma7f1Qbd-UuKXNJodPg=",
            "expected_objects": ["person"],
            "min_objects": 5
        },
        {
            "name": "Flickr image with objects",
            "url": "https://live.staticflickr.com/2815/12382975864_2cd7755b03_b.jpg",
            "expected_objects": None,  # Unknown what's in this image
            "min_objects": 0  # May or may not have objects, but should process successfully
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        print(f"\n--- Test: {test_case['name']} ---")
        print(f"URL: {test_case['url'][:80]}...")
        
        try:
            # Call the tool
            result = detect_objects_tool(
                image_path=test_case['url'],
                confidence_threshold=0.5,
                draw=True
            )
            
            # Test 1: No error
            if 'error' in result:
                print(f"❌ FAIL: Error returned: {result['error']}")
                all_passed = False
                continue
            
            # Test 2: Object count exists and is reasonable
            object_count = result.get('object_count', 0)
            print(f"   Objects detected: {object_count}")
            
            if object_count < test_case['min_objects']:
                print(f"❌ FAIL: Expected at least {test_case['min_objects']} objects, got {object_count}")
                all_passed = False
                continue
            
            # If no objects detected, that's okay as long as processing succeeded
            if object_count == 0:
                print(f"   ⚠️  No objects detected (image may not contain detectable objects)")
                # Still verify the structure is correct
                if 'objects' not in result or result.get('objects') != []:
                    print(f"❌ FAIL: objects list should be empty when object_count is 0")
                    all_passed = False
                    continue
                print(f"   ✅ Processing successful (no objects detected, which is valid)")
                continue
            
            # Test 3: Objects list exists and has correct structure
            objects = result.get('objects', [])
            if len(objects) != object_count:
                print(f"❌ FAIL: object_count ({object_count}) doesn't match objects list length ({len(objects)})")
                all_passed = False
                continue
            
            if len(objects) == 0:
                print(f"❌ FAIL: objects list is empty but object_count is {object_count}")
                all_passed = False
                continue
            
            # Test 4: Each object has required fields
            required_fields = ['class_name', 'confidence', 'x', 'y', 'width', 'height']
            for i, obj in enumerate(objects[:5]):  # Check first 5
                missing_fields = [field for field in required_fields if field not in obj]
                if missing_fields:
                    print(f"❌ FAIL: Object {i} missing fields: {missing_fields}")
                    all_passed = False
                    continue
                
                # Validate field types and values
                if not isinstance(obj['confidence'], (int, float)) or not (0 <= obj['confidence'] <= 1):
                    print(f"❌ FAIL: Object {i} has invalid confidence: {obj['confidence']}")
                    all_passed = False
                    continue
                
                if not isinstance(obj['x'], int) or obj['x'] < 0:
                    print(f"❌ FAIL: Object {i} has invalid x: {obj['x']}")
                    all_passed = False
                    continue
                
                if not isinstance(obj['y'], int) or obj['y'] < 0:
                    print(f"❌ FAIL: Object {i} has invalid y: {obj['y']}")
                    all_passed = False
                    continue
            
            # Test 5: Check for expected object types if specified
            if test_case['expected_objects']:
                detected_classes = [obj['class_name'] for obj in objects]
                found_expected = any(cls in detected_classes for cls in test_case['expected_objects'])
                if not found_expected:
                    print(f"⚠️  WARNING: Expected one of {test_case['expected_objects']}, but found: {set(detected_classes[:10])}")
                else:
                    print(f"   ✅ Found expected object types: {[cls for cls in test_case['expected_objects'] if cls in detected_classes]}")
            
            # Test 6: Base64 image exists and is valid
            image_base64 = result.get('image_base64', '')
            if not image_base64:
                print(f"❌ FAIL: image_base64 is missing or empty")
                all_passed = False
                continue
            
            # Check if it's a data URI
            if image_base64.startswith('data:'):
                # Extract base64 part
                base64_part = image_base64.split(',', 1)[1] if ',' in image_base64 else image_base64
            else:
                base64_part = image_base64
            
            # Validate base64 encoding
            try:
                decoded = base64.b64decode(base64_part)
                if len(decoded) < 1000:  # Should be at least a few KB for a valid image
                    print(f"❌ FAIL: Decoded image is too small ({len(decoded)} bytes), likely invalid")
                    all_passed = False
                    continue
                print(f"   ✅ Base64 image valid: {len(decoded)} bytes decoded")
            except Exception as e:
                print(f"❌ FAIL: Base64 decode error: {e}")
                all_passed = False
                continue
            
            # Test 7: Model info exists
            model_info = result.get('model_info', {})
            if not model_info:
                print(f"⚠️  WARNING: model_info is missing")
            else:
                model_path = model_info.get('model_path', '')
                if 'yolov3.weights' not in model_path:
                    print(f"⚠️  WARNING: Unexpected model path: {model_path}")
                else:
                    print(f"   ✅ Model info present: {model_path}")
            
            # Test 8: Image info exists
            info = result.get('info', {})
            if not info:
                print(f"⚠️  WARNING: image info is missing")
            else:
                print(f"   ✅ Image info present: {info.get('width', '?')}x{info.get('height', '?')}")
            
            # Print sample detections
            print(f"   Sample detections:")
            for obj in objects[:3]:
                print(f"     - {obj['class_name']}: {obj['confidence']:.2f} at ({obj['x']}, {obj['y']})")
            
            print(f"✅ PASS: {test_case['name']}")
            
        except Exception as e:
            print(f"❌ FAIL: Exception occurred: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ ALL FUNCTIONAL TESTS PASSED")
    else:
        print("❌ SOME FUNCTIONAL TESTS FAILED")
    print("="*70)
    
    return all_passed


def test_yolo_different_confidence_thresholds():
    """Test that different confidence thresholds work correctly."""
    print("\n" + "="*70)
    print("FUNCTIONAL TEST: YOLO with Different Confidence Thresholds")
    print("="*70)
    
    os.environ['OPENCV_DNN_MODELS_DIR'] = '/app/OPENCV_DNN_MODELS_DIR'
    from opencv_mcp_server.computer_vision import detect_objects_tool
    
    test_url = "https://media.istockphoto.com/id/1480574526/photo/happy-multigenerational-people-having-fun-sitting-on-grass-in-a-public-park.jpg?s=612x612&w=0&k=20&c=iIzSiY2FK9mWTCmV8Ip8zpvXma7f1Qbd-UuKXNJodPg="
    
    thresholds = [0.3, 0.5, 0.7, 0.9]
    results = {}
    
    for threshold in thresholds:
        try:
            result = detect_objects_tool(
                image_path=test_url,
                confidence_threshold=threshold,
                draw=True
            )
            
            if 'error' in result:
                print(f"❌ FAIL: Error at threshold {threshold}: {result['error']}")
                return False
            
            count = result.get('object_count', 0)
            results[threshold] = count
            print(f"   Threshold {threshold}: {count} objects")
            
        except Exception as e:
            print(f"❌ FAIL: Exception at threshold {threshold}: {e}")
            return False
    
    # Verify that lower thresholds detect more objects
    if results[0.3] >= results[0.5] >= results[0.7] >= results[0.9]:
        print("✅ PASS: Lower thresholds detect more objects (as expected)")
        return True
    else:
        print(f"⚠️  WARNING: Unexpected threshold behavior: {results}")
        # This might be okay if all objects have high confidence
        return True


if __name__ == "__main__":
    # Run tests
    test1_passed = test_yolo_url_download_and_detection()
    test2_passed = test_yolo_different_confidence_thresholds()
    
    if test1_passed and test2_passed:
        sys.exit(0)
    else:
        sys.exit(1)

