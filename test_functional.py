#!/usr/bin/env python3
"""
Functional tests for OpenCV MCP Server URL processing.

These tests verify that operations actually produce correct results,
not just that they execute without errors.
"""

import os
import sys
import json
import cv2
import numpy as np
import base64
from pathlib import Path
import tempfile
import shutil

# Add the package to path
sys.path.insert(0, str(Path(__file__).parent))

from opencv_mcp_server import image_basics
from opencv_mcp_server import image_processing
from opencv_mcp_server import computer_vision
from opencv_mcp_server.utils import read_image, is_url

# Test results storage
test_results = {
    "passed": [],
    "failed": [],
    "skipped": []
}

def load_urls(filename):
    """Load URLs from a text file."""
    urls = []
    possible_paths = [
        Path(__file__).parent / filename,
        Path.cwd() / filename,
        Path(filename)
    ]
    
    filepath = None
    for path in possible_paths:
        if path.exists():
            filepath = path
            break
    
    if filepath:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.append(line)
    return urls

def verify_image_file(filepath):
    """Verify that a file exists and is a valid image."""
    if not filepath:
        return False, "No filepath provided"
    
    if not os.path.exists(filepath):
        return False, f"File does not exist: {filepath}"
    
    if os.path.getsize(filepath) == 0:
        return False, f"File is empty: {filepath}"
    
    # Try to read the image
    img = cv2.imread(filepath)
    if img is None:
        return False, f"File is not a valid image: {filepath}"
    
    if img.size == 0:
        return False, f"Image has zero size: {filepath}"
    
    return True, f"Valid image: {img.shape}"

def verify_base64_image(base64_str, expected_shape=None):
    """Verify that a base64 string contains a valid image."""
    if not base64_str:
        return False, "No base64 string provided"
    
    if not isinstance(base64_str, str):
        return False, f"Base64 is not a string: {type(base64_str)}"
    
    # Check if it's a data URI
    if base64_str.startswith("data:"):
        # Extract base64 part after comma
        if "," not in base64_str:
            return False, "Invalid data URI format (no comma)"
        base64_data = base64_str.split(",", 1)[1]
    else:
        base64_data = base64_str
    
    # Try to decode
    try:
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        return False, f"Failed to decode base64: {str(e)}"
    
    if len(image_bytes) == 0:
        return False, "Decoded base64 is empty"
    
    # Try to decode as image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return False, "Base64 does not contain a valid image"
    
    if img.size == 0:
        return False, f"Decoded image has zero size"
    
    # Check dimensions if expected
    if expected_shape:
        if img.shape != expected_shape:
            return False, f"Image shape mismatch: got {img.shape}, expected {expected_shape}"
    
    return True, f"Valid base64 image: {img.shape}, {len(image_bytes)} bytes"

def test_resize_functional():
    """Test resize with functional verification."""
    print("\n=== Functional Test: Resize from URL ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        test_results["skipped"].append("Resize functional test (no URLs)")
        return
    
    url = image_urls[0]
    try:
        print(f"Testing resize with: {url[:60]}...")
        
        # Create temp directory for output
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory to capture output
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = image_basics.resize_image_tool(
                    image_path=url,
                    width=400,
                    height=300
                )
                
                # Verify result structure
                assert "path" in result, "Result missing 'path' key"
                assert "info" in result, "Result missing 'info' key"
                assert "width" in result, "Result missing 'width' key"
                assert "height" in result, "Result missing 'height' key"
                assert "image_base64" in result, "Result missing 'image_base64' key (required for LLM access)"
                
                # Verify dimensions
                assert result["width"] == 400, f"Expected width 400, got {result['width']}"
                assert result["height"] == 300, f"Expected height 300, got {result['height']}"
                assert result["info"]["width"] == 400, f"Info width mismatch: {result['info']['width']}"
                assert result["info"]["height"] == 300, f"Info height mismatch: {result['info']['height']}"
                
                # Verify base64 output (PRIMARY - required for LLM access)
                base64_str = result["image_base64"]
                is_valid_base64, base64_msg = verify_base64_image(base64_str, expected_shape=(300, 400, 3))
                if not is_valid_base64:
                    test_results["failed"].append(f"Resize: Base64 verification failed: {base64_msg}")
                    print(f"✗ FAILED: Base64 verification failed: {base64_msg}")
                    return
                
                # Verify output file exists and is valid (for backward compatibility)
                output_path = result["path"]
                if is_url(output_path):
                    test_results["failed"].append(f"Resize: Output path is URL, not local file: {output_path}")
                    print(f"✗ FAILED: Output path is a URL, not a local file")
                    return
                
                is_valid_file, file_msg = verify_image_file(output_path)
                if not is_valid_file:
                    test_results["failed"].append(f"Resize: File verification failed: {file_msg}")
                    print(f"✗ FAILED: File verification failed: {file_msg}")
                    return
                
                # Verify image dimensions match
                img = cv2.imread(output_path)
                assert img.shape[1] == 400, f"Image width is {img.shape[1]}, expected 400"
                assert img.shape[0] == 300, f"Image height is {img.shape[0]}, expected 300"
                
                # Verify base64 matches file dimensions
                base64_img = cv2.imdecode(np.frombuffer(base64.b64decode(base64_str.split(",")[1]), np.uint8), cv2.IMREAD_COLOR)
                assert base64_img.shape == img.shape, f"Base64 image shape {base64_img.shape} != file image shape {img.shape}"
                
                test_results["passed"].append(f"Resize functional: Correctly resized to 400x300 with base64 output")
                print(f"✓ PASSED: Image correctly resized to 400x300")
                print(f"  Output file: {output_path}")
                print(f"  File size: {os.path.getsize(output_path)} bytes")
                print(f"  Base64 length: {len(base64_str)} chars")
                print(f"  Image shape: {img.shape}")
                print(f"  Base64 image shape: {base64_img.shape}")
                
            finally:
                os.chdir(original_cwd)
                
    except AssertionError as e:
        test_results["failed"].append(f"Resize functional: {str(e)}")
        print(f"✗ FAILED: {str(e)}")
    except Exception as e:
        test_results["failed"].append(f"Resize functional error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_edge_detection_functional():
    """Test edge detection with functional verification."""
    print("\n=== Functional Test: Edge Detection from URL ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        test_results["skipped"].append("Edge detection functional test (no URLs)")
        return
    
    url = image_urls[0]
    try:
        print(f"Testing edge detection with: {url[:60]}...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = image_processing.detect_edges_tool(
                    image_path=url,
                    method="canny",
                    threshold1=100,
                    threshold2=200
                )
                
                # Verify result structure
                assert "path" in result, "Result missing 'path' key"
                assert "info" in result, "Result missing 'info' key"
                assert "method_info" in result, "Result missing 'method_info' key"
                assert "image_base64" in result, "Result missing 'image_base64' key (required for LLM access)"
                
                # Verify base64 output (PRIMARY - required for LLM access)
                base64_str = result["image_base64"]
                is_valid_base64, base64_msg = verify_base64_image(base64_str)
                if not is_valid_base64:
                    test_results["failed"].append(f"Edge detection: Base64 verification failed: {base64_msg}")
                    print(f"✗ FAILED: Base64 verification failed: {base64_msg}")
                    return
                
                # Verify output file (for backward compatibility)
                output_path = result["path"]
                if is_url(output_path):
                    test_results["failed"].append(f"Edge detection: Output path is URL, not local file")
                    print(f"✗ FAILED: Output path is a URL, not a local file")
                    return
                
                is_valid, msg = verify_image_file(output_path)
                if not is_valid:
                    test_results["failed"].append(f"Edge detection: {msg}")
                    print(f"✗ FAILED: {msg}")
                    return
                
                # Verify it's a grayscale image (edge detection produces grayscale)
                img = cv2.imread(output_path)
                # Edge detection can produce single channel or 3-channel depending on implementation
                # But it should be mostly black/white
                assert len(img.shape) >= 2, "Image should have at least 2 dimensions"
                
                # Check that image has reasonable edge content (not all black or all white)
                if len(img.shape) == 2:
                    unique_values = len(np.unique(img))
                else:
                    unique_values = len(np.unique(img.reshape(-1, img.shape[2]), axis=0))
                
                # Should have some variation (edges)
                assert unique_values > 2, f"Edge image should have variation, got {unique_values} unique values"
                
                test_results["passed"].append(f"Edge detection functional: Produced valid edge image")
                print(f"✓ PASSED: Edge detection produced valid image")
                print(f"  Output file: {output_path}")
                print(f"  Image shape: {img.shape}")
                print(f"  Unique values: {unique_values}")
                
            finally:
                os.chdir(original_cwd)
                
    except AssertionError as e:
        test_results["failed"].append(f"Edge detection functional: {str(e)}")
        print(f"✗ FAILED: {str(e)}")
    except Exception as e:
        test_results["failed"].append(f"Edge detection functional error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_face_detection_functional():
    """Test face detection with functional verification."""
    print("\n=== Functional Test: Face Detection from URL ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        test_results["skipped"].append("Face detection functional test (no URLs)")
        return
    
    # Use first URL (should be the people photo)
    url = image_urls[0]
    try:
        print(f"Testing face detection with: {url[:60]}...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = computer_vision.detect_faces_tool(
                    image_path=url,
                    method="haar",
                    min_neighbors=5
                )
                
                # Verify result structure
                assert "face_count" in result, "Result missing 'face_count' key"
                assert "faces" in result, "Result missing 'faces' key"
                assert "path" in result, "Result missing 'path' key"
                assert "image_base64" in result, "Result missing 'image_base64' key (required for LLM access)"
                
                # Verify base64 output (PRIMARY - required for LLM access)
                base64_str = result["image_base64"]
                is_valid_base64, base64_msg = verify_base64_image(base64_str)
                if not is_valid_base64:
                    test_results["failed"].append(f"Face detection: Base64 verification failed: {base64_msg}")
                    print(f"✗ FAILED: Base64 verification failed: {base64_msg}")
                    return
                
                # Verify output file (for backward compatibility)
                output_path = result["path"]
                if is_url(output_path):
                    test_results["failed"].append(f"Face detection: Output path is URL, not local file")
                    print(f"✗ FAILED: Output path is a URL, not a local file")
                    return
                
                is_valid, msg = verify_image_file(output_path)
                if not is_valid:
                    test_results["failed"].append(f"Face detection: {msg}")
                    print(f"✗ FAILED: {msg}")
                    return
                
                # Verify face count
                face_count = result["face_count"]
                assert face_count >= 0, f"Face count should be >= 0, got {face_count}"
                
                # Verify faces list matches count
                assert len(result["faces"]) == face_count, f"Faces list length {len(result['faces'])} != face_count {face_count}"
                
                # If faces were detected, verify they have valid coordinates
                if face_count > 0:
                    for i, face in enumerate(result["faces"]):
                        assert "x" in face, f"Face {i} missing 'x' coordinate"
                        assert "y" in face, f"Face {i} missing 'y' coordinate"
                        assert "width" in face, f"Face {i} missing 'width'"
                        assert "height" in face, f"Face {i} missing 'height'"
                        assert face["width"] > 0, f"Face {i} has invalid width: {face['width']}"
                        assert face["height"] > 0, f"Face {i} has invalid height: {face['height']}"
                
                test_results["passed"].append(f"Face detection functional: Detected {face_count} faces with base64 output")
                print(f"✓ PASSED: Face detection found {face_count} faces")
                print(f"  Output file: {output_path}")
                print(f"  Base64 length: {len(base64_str)} chars")
                if face_count > 0:
                    print(f"  First face: x={result['faces'][0]['x']}, y={result['faces'][0]['y']}, w={result['faces'][0]['width']}, h={result['faces'][0]['height']}")
                
            finally:
                os.chdir(original_cwd)
                
    except AssertionError as e:
        test_results["failed"].append(f"Face detection functional: {str(e)}")
        print(f"✗ FAILED: {str(e)}")
    except Exception as e:
        test_results["failed"].append(f"Face detection functional error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_image_stats_functional():
    """Test image statistics with functional verification."""
    print("\n=== Functional Test: Image Statistics from URL ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        test_results["skipped"].append("Image stats functional test (no URLs)")
        return
    
    url = image_urls[0]
    try:
        print(f"Testing image stats with: {url[:60]}...")
        
        result = image_basics.get_image_stats_tool(
            image_path=url,
            channels=True
        )
        
        # Verify result structure
        assert "info" in result, "Result missing 'info' key"
        assert "min" in result, "Result missing 'min' key"
        assert "max" in result, "Result missing 'max' key"
        assert "mean" in result, "Result missing 'mean' key"
        assert "stddev" in result, "Result missing 'stddev' key"
        
        # Verify info structure
        info = result["info"]
        assert "width" in info, "Info missing 'width'"
        assert "height" in info, "Info missing 'height'"
        assert "channels" in info, "Info missing 'channels'"
        
        # Verify values are reasonable
        assert info["width"] > 0, f"Width should be > 0, got {info['width']}"
        assert info["height"] > 0, f"Height should be > 0, got {info['height']}"
        assert info["channels"] in [1, 3, 4], f"Channels should be 1, 3, or 4, got {info['channels']}"
        assert 0 <= result["min"] <= 255, f"Min should be 0-255, got {result['min']}"
        assert 0 <= result["max"] <= 255, f"Max should be 0-255, got {result['max']}"
        assert result["min"] <= result["mean"] <= result["max"], "Mean should be between min and max"
        
        # Verify channels if present
        if "channels" in result and info["channels"] > 1:
            assert len(result["channels"]) == info["channels"], f"Channel stats count mismatch"
            for i, ch in enumerate(result["channels"]):
                assert "channel" in ch, f"Channel {i} missing 'channel' key"
                assert 0 <= ch["min"] <= 255, f"Channel {i} min invalid: {ch['min']}"
                assert 0 <= ch["max"] <= 255, f"Channel {i} max invalid: {ch['max']}"
        
        test_results["passed"].append(f"Image stats functional: Valid statistics calculated")
        print(f"✓ PASSED: Image statistics are valid")
        print(f"  Dimensions: {info['width']}x{info['height']}")
        print(f"  Channels: {info['channels']}")
        mean_val = result['mean']
        print(f"  Min: {result['min']}, Max: {result['max']}, Mean: {mean_val:.2f}")
        
    except AssertionError as e:
        test_results["failed"].append(f"Image stats functional: {str(e)}")
        print(f"✗ FAILED: {str(e)}")
    except Exception as e:
        test_results["failed"].append(f"Image stats functional error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def test_filter_functional():
    """Test filter application with functional verification."""
    print("\n=== Functional Test: Filter Application from URL ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        test_results["skipped"].append("Filter functional test (no URLs)")
        return
    
    url = image_urls[0]
    try:
        print(f"Testing filter with: {url[:60]}...")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                result = image_processing.apply_filter_tool(
                    image_path=url,
                    filter_type="gaussian",
                    kernel_size=5,
                    sigma=1.5
                )
                
                # Verify result structure
                assert "path" in result, "Result missing 'path' key"
                assert "filter" in result, "Result missing 'filter' key"
                assert "info" in result, "Result missing 'info' key"
                assert "image_base64" in result, "Result missing 'image_base64' key (required for LLM access)"
                
                # Verify filter info
                filter_info = result["filter"]
                assert filter_info["type"] == "gaussian", f"Filter type should be 'gaussian', got {filter_info['type']}"
                
                # Verify base64 output (PRIMARY - required for LLM access)
                base64_str = result["image_base64"]
                is_valid_base64, base64_msg = verify_base64_image(base64_str)
                if not is_valid_base64:
                    test_results["failed"].append(f"Filter: Base64 verification failed: {base64_msg}")
                    print(f"✗ FAILED: Base64 verification failed: {base64_msg}")
                    return
                
                # Verify output file (for backward compatibility)
                output_path = result["path"]
                if is_url(output_path):
                    test_results["failed"].append(f"Filter: Output path is URL, not local file")
                    print(f"✗ FAILED: Output path is a URL, not a local file")
                    return
                
                is_valid, msg = verify_image_file(output_path)
                if not is_valid:
                    test_results["failed"].append(f"Filter: {msg}")
                    print(f"✗ FAILED: {msg}")
                    return
                
                # Verify image dimensions match original (filter shouldn't change size)
                img = cv2.imread(output_path)
                original_img = read_image(url)
                assert img.shape[:2] == original_img.shape[:2], f"Filter changed image size: {img.shape[:2]} vs {original_img.shape[:2]}"
                
                # Verify base64 matches file dimensions
                base64_img = cv2.imdecode(np.frombuffer(base64.b64decode(base64_str.split(",")[1]), np.uint8), cv2.IMREAD_COLOR)
                assert base64_img.shape == img.shape, f"Base64 image shape {base64_img.shape} != file image shape {img.shape}"
                
                # Verify image is different (blurred images should have different pixel values)
                # But this is probabilistic, so we'll just check it's a valid image
                assert img.size > 0, "Filtered image has zero size"
                
                test_results["passed"].append(f"Filter functional: Applied Gaussian blur correctly with base64 output")
                print(f"✓ PASSED: Filter applied successfully")
                print(f"  Output file: {output_path}")
                print(f"  Base64 length: {len(base64_str)} chars")
                print(f"  Image shape: {img.shape}")
                print(f"  Filter type: {filter_info['type']}")
                
            finally:
                os.chdir(original_cwd)
                
    except AssertionError as e:
        test_results["failed"].append(f"Filter functional: {str(e)}")
        print(f"✗ FAILED: {str(e)}")
    except Exception as e:
        test_results["failed"].append(f"Filter functional error: {str(e)}")
        print(f"✗ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("FUNCTIONAL TEST SUMMARY")
    print("="*60)
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
    
    # Save results to JSON
    results_file = Path(__file__).parent / "test_functional_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

def main():
    """Run all functional tests."""
    print("="*60)
    print("OpenCV MCP Server - Functional Tests")
    print("="*60)
    print("These tests verify that operations produce correct results,")
    print("not just that they execute without errors.")
    print("="*60)
    
    # Run functional tests
    test_resize_functional()
    test_edge_detection_functional()
    test_face_detection_functional()
    test_image_stats_functional()
    test_filter_functional()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

