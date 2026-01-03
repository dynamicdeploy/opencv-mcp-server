#!/usr/bin/env python3
"""
Comprehensive functional tests that verify actual output quality and correctness.

This script tests all image URLs and verifies the actual output files.
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

sys.path.insert(0, str(Path(__file__).parent))

from opencv_mcp_server import image_basics, image_processing, computer_vision
from opencv_mcp_server.utils import read_image, is_url

test_results = {
    "passed": [],
    "failed": [],
    "skipped": [],
    "details": {}
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

def verify_base64_image(base64_str, expected_shape=None):
    """Verify that a base64 string contains a valid image."""
    if not base64_str:
        return False, ["No base64 string provided"]
    
    if not isinstance(base64_str, str):
        return False, [f"Base64 is not a string: {type(base64_str)}"]
    
    # Check if it's a data URI
    if base64_str.startswith("data:"):
        if "," not in base64_str:
            return False, ["Invalid data URI format (no comma)"]
        base64_data = base64_str.split(",", 1)[1]
    else:
        base64_data = base64_str
    
    # Try to decode
    try:
        image_bytes = base64.b64decode(base64_data)
    except Exception as e:
        return False, [f"Failed to decode base64: {str(e)}"]
    
    if len(image_bytes) == 0:
        return False, ["Decoded base64 is empty"]
    
    # Try to decode as image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        return False, ["Base64 does not contain a valid image"]
    
    if img.size == 0:
        return False, ["Decoded image has zero size"]
    
    # Check dimensions if expected
    if expected_shape:
        if img.shape != expected_shape:
            return False, [f"Image shape mismatch: got {img.shape}, expected {expected_shape}"]
    
    # Check image is not all zeros or all same value
    if len(img.shape) == 2:
        unique_vals = len(np.unique(img))
    else:
        unique_vals = len(np.unique(img.reshape(-1, img.shape[2]), axis=0))
    
    if unique_vals < 2:
        return False, [f"Image has no variation (all same value): {unique_vals} unique values"]
    
    return True, []

def verify_output_file(filepath, expected_shape=None, min_size_bytes=1000):
    """Comprehensively verify an output file."""
    issues = []
    
    if not filepath:
        return False, ["No filepath provided"]
    
    if is_url(filepath):
        return False, [f"Output path is a URL, not a local file: {filepath}"]
    
    if not os.path.exists(filepath):
        return False, [f"File does not exist: {filepath}"]
    
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        return False, [f"File is empty: {filepath}"]
    
    if file_size < min_size_bytes:
        issues.append(f"File is suspiciously small: {file_size} bytes (expected at least {min_size_bytes})")
    
    # Try to read the image
    img = cv2.imread(filepath)
    if img is None:
        return False, [f"File is not a valid image: {filepath}"]
    
    if img.size == 0:
        return False, [f"Image has zero size: {filepath}"]
    
    # Check dimensions if expected
    if expected_shape:
        if img.shape != expected_shape:
            issues.append(f"Image shape mismatch: got {img.shape}, expected {expected_shape}")
    
    # Check image is not all zeros or all same value (should have some variation)
    if len(img.shape) == 2:
        unique_vals = len(np.unique(img))
    else:
        unique_vals = len(np.unique(img.reshape(-1, img.shape[2]), axis=0))
    
    if unique_vals < 2:
        issues.append(f"Image has no variation (all same value): {unique_vals} unique values")
    
    return len(issues) == 0, issues

def test_resize_comprehensive():
    """Test resize with all URLs and verify outputs."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Resize from URLs")
    print("="*70)
    
    image_urls = load_urls("image_urls.txt")
    if not image_urls:
        test_results["skipped"].append("Resize comprehensive (no URLs)")
        return
    
    test_results["details"]["resize"] = {}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            for i, url in enumerate(image_urls, 1):
                print(f"\n[{i}/{len(image_urls)}] Testing: {url[:70]}...")
                test_key = f"url_{i}"
                test_results["details"]["resize"][test_key] = {
                    "url": url,
                    "status": "unknown"
                }
                
                try:
                    # Read original to get dimensions
                    original_img = read_image(url)
                    orig_h, orig_w = original_img.shape[:2]
                    
                    # Resize to specific dimensions
                    target_w, target_h = 400, 300
                    result = image_basics.resize_image_tool(url, target_w, target_h)
                    
                    # Verify result structure
                    assert "path" in result, "Missing 'path' in result"
                    assert "info" in result, "Missing 'info' in result"
                    assert "image_base64" in result, "Missing 'image_base64' in result (required for LLM access)"
                    assert result["width"] == target_w, f"Width mismatch: {result['width']} != {target_w}"
                    assert result["height"] == target_h, f"Height mismatch: {result['height']} != {target_h}"
                    
                    # Verify base64 output (PRIMARY - required for LLM access)
                    base64_str = result["image_base64"]
                    is_valid_base64, base64_issues = verify_base64_image(base64_str, expected_shape=(target_h, target_w, 3))
                    if not is_valid_base64:
                        test_results["failed"].append(f"Resize URL {i}: Base64 verification failed: {', '.join(base64_issues)}")
                        test_results["details"]["resize"][test_key]["status"] = "failed"
                        test_results["details"]["resize"][test_key]["error"] = f"Base64: {', '.join(base64_issues)}"
                        print(f"  ✗ FAILED: Base64 verification failed: {', '.join(base64_issues)}")
                        continue
                    
                    # Verify output file (for backward compatibility)
                    output_path = result["path"]
                    is_valid, issues = verify_output_file(output_path, expected_shape=(target_h, target_w, 3))
                    if not is_valid:
                        test_results["failed"].append(f"Resize URL {i}: File verification failed: {', '.join(issues)}")
                        test_results["details"]["resize"][test_key]["status"] = "failed"
                        test_results["details"]["resize"][test_key]["error"] = f"File: {', '.join(issues)}"
                        print(f"  ✗ FAILED: File verification failed: {', '.join(issues)}")
                        continue
                    
                    # Verify image dimensions match
                    img = cv2.imread(output_path)
                    assert img.shape[1] == target_w, f"Image width {img.shape[1]} != {target_w}"
                    assert img.shape[0] == target_h, f"Image height {img.shape[0]} != {target_h}"
                    
                    # Verify base64 matches file
                    base64_img = cv2.imdecode(np.frombuffer(base64.b64decode(base64_str.split(",")[1]), np.uint8), cv2.IMREAD_COLOR)
                    assert base64_img.shape == img.shape, f"Base64 image shape {base64_img.shape} != file shape {img.shape}"
                    
                    # Check image quality (not all black/white)
                    mean_val = np.mean(img)
                    assert 10 < mean_val < 245, f"Image appears corrupted (mean={mean_val:.2f})"
                    
                    test_results["passed"].append(f"Resize URL {i}: {url[:50]}... (with base64)")
                    test_results["details"]["resize"][test_key]["status"] = "passed"
                    test_results["details"]["resize"][test_key]["output_path"] = output_path
                    test_results["details"]["resize"][test_key]["base64_length"] = len(base64_str)
                    test_results["details"]["resize"][test_key]["original_size"] = f"{orig_w}x{orig_h}"
                    test_results["details"]["resize"][test_key]["output_size"] = f"{target_w}x{target_h}"
                    test_results["details"]["resize"][test_key]["file_size"] = os.path.getsize(output_path)
                    print(f"  ✓ PASSED: {target_w}x{target_h}, file: {os.path.getsize(output_path)} bytes, base64: {len(base64_str)} chars")
                    
                except Exception as e:
                    test_results["failed"].append(f"Resize URL {i}: {str(e)}")
                    test_results["details"]["resize"][test_key]["status"] = "error"
                    test_results["details"]["resize"][test_key]["error"] = str(e)
                    print(f"  ✗ ERROR: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        finally:
            os.chdir(original_cwd)

def test_edge_detection_comprehensive():
    """Test edge detection with all URLs and verify outputs."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Edge Detection from URLs")
    print("="*70)
    
    image_urls = load_urls("image_urls.txt")
    if not image_urls:
        test_results["skipped"].append("Edge detection comprehensive (no URLs)")
        return
    
    test_results["details"]["edge_detection"] = {}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            for i, url in enumerate(image_urls[:3], 1):  # Test first 3 to save time
                print(f"\n[{i}/3] Testing: {url[:70]}...")
                test_key = f"url_{i}"
                test_results["details"]["edge_detection"][test_key] = {"url": url, "status": "unknown"}
                
                try:
                    result = image_processing.detect_edges_tool(url, method="canny", threshold1=100, threshold2=200)
                    
                    assert "path" in result, "Missing 'path'"
                    assert "image_base64" in result, "Missing 'image_base64' (required for LLM access)"
                    
                    # Verify base64 output (PRIMARY)
                    base64_str = result["image_base64"]
                    is_valid_base64, base64_issues = verify_base64_image(base64_str)
                    if not is_valid_base64:
                        test_results["failed"].append(f"Edge detection URL {i}: Base64 verification failed: {', '.join(base64_issues)}")
                        test_results["details"]["edge_detection"][test_key]["status"] = "failed"
                        test_results["details"]["edge_detection"][test_key]["error"] = f"Base64: {', '.join(base64_issues)}"
                        print(f"  ✗ FAILED: Base64 verification failed: {', '.join(base64_issues)}")
                        continue
                    
                    # Verify output file (for backward compatibility)
                    output_path = result["path"]
                    is_valid, issues = verify_output_file(output_path, min_size_bytes=5000)
                    if not is_valid:
                        test_results["failed"].append(f"Edge detection URL {i}: File verification failed: {', '.join(issues)}")
                        test_results["details"]["edge_detection"][test_key]["status"] = "failed"
                        test_results["details"]["edge_detection"][test_key]["error"] = f"File: {', '.join(issues)}"
                        print(f"  ✗ FAILED: File verification failed: {', '.join(issues)}")
                        continue
                    
                    # Verify it's an edge image (should have variation)
                    img = cv2.imread(output_path)
                    unique_vals = len(np.unique(img.reshape(-1, img.shape[2]), axis=0)) if len(img.shape) == 3 else len(np.unique(img))
                    assert unique_vals > 10, f"Edge image lacks variation: {unique_vals} unique values"
                    
                    test_results["passed"].append(f"Edge detection URL {i}: {url[:50]}... (with base64)")
                    test_results["details"]["edge_detection"][test_key]["status"] = "passed"
                    test_results["details"]["edge_detection"][test_key]["output_path"] = output_path
                    test_results["details"]["edge_detection"][test_key]["base64_length"] = len(base64_str)
                    test_results["details"]["edge_detection"][test_key]["unique_values"] = unique_vals
                    test_results["details"]["edge_detection"][test_key]["file_size"] = os.path.getsize(output_path)
                    print(f"  ✓ PASSED: {unique_vals} unique values, file: {os.path.getsize(output_path)} bytes, base64: {len(base64_str)} chars")
                    
                except Exception as e:
                    test_results["failed"].append(f"Edge detection URL {i}: {str(e)}")
                    test_results["details"]["edge_detection"][test_key]["status"] = "error"
                    test_results["details"]["edge_detection"][test_key]["error"] = str(e)
                    print(f"  ✗ ERROR: {str(e)}")
        
        finally:
            os.chdir(original_cwd)

def test_face_detection_comprehensive():
    """Test face detection with all URLs and verify outputs."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Face Detection from URLs")
    print("="*70)
    
    image_urls = load_urls("image_urls.txt")
    if not image_urls:
        test_results["skipped"].append("Face detection comprehensive (no URLs)")
        return
    
    test_results["details"]["face_detection"] = {}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        
        try:
            for i, url in enumerate(image_urls[:3], 1):  # Test first 3
                print(f"\n[{i}/3] Testing: {url[:70]}...")
                test_key = f"url_{i}"
                test_results["details"]["face_detection"][test_key] = {"url": url, "status": "unknown"}
                
                try:
                    result = computer_vision.detect_faces_tool(url, method="haar", min_neighbors=5)
                    
                    assert "path" in result, "Missing 'path'"
                    assert "face_count" in result, "Missing 'face_count'"
                    assert "image_base64" in result, "Missing 'image_base64' (required for LLM access)"
                    
                    # Verify base64 output (PRIMARY)
                    base64_str = result["image_base64"]
                    is_valid_base64, base64_issues = verify_base64_image(base64_str)
                    if not is_valid_base64:
                        test_results["failed"].append(f"Face detection URL {i}: Base64 verification failed: {', '.join(base64_issues)}")
                        test_results["details"]["face_detection"][test_key]["status"] = "failed"
                        test_results["details"]["face_detection"][test_key]["error"] = f"Base64: {', '.join(base64_issues)}"
                        print(f"  ✗ FAILED: Base64 verification failed: {', '.join(base64_issues)}")
                        continue
                    
                    # Verify output file (for backward compatibility)
                    output_path = result["path"]
                    is_valid, issues = verify_output_file(output_path, min_size_bytes=5000)
                    if not is_valid:
                        test_results["failed"].append(f"Face detection URL {i}: File verification failed: {', '.join(issues)}")
                        test_results["details"]["face_detection"][test_key]["status"] = "failed"
                        test_results["details"]["face_detection"][test_key]["error"] = f"File: {', '.join(issues)}"
                        print(f"  ✗ FAILED: File verification failed: {', '.join(issues)}")
                        continue
                    
                    face_count = result["face_count"]
                    assert face_count >= 0, f"Face count should be >= 0, got {face_count}"
                    
                    # Verify faces data
                    assert len(result["faces"]) == face_count, "Faces list length mismatch"
                    
                    if face_count > 0:
                        for face in result["faces"]:
                            assert "x" in face and "y" in face and "width" in face and "height" in face
                            assert face["width"] > 0 and face["height"] > 0
                    
                    test_results["passed"].append(f"Face detection URL {i}: {face_count} faces found (with base64)")
                    test_results["details"]["face_detection"][test_key]["status"] = "passed"
                    test_results["details"]["face_detection"][test_key]["output_path"] = output_path
                    test_results["details"]["face_detection"][test_key]["base64_length"] = len(base64_str)
                    test_results["details"]["face_detection"][test_key]["face_count"] = face_count
                    test_results["details"]["face_detection"][test_key]["file_size"] = os.path.getsize(output_path)
                    print(f"  ✓ PASSED: {face_count} faces detected, file: {os.path.getsize(output_path)} bytes, base64: {len(base64_str)} chars")
                    
                except Exception as e:
                    test_results["failed"].append(f"Face detection URL {i}: {str(e)}")
                    test_results["details"]["face_detection"][test_key]["status"] = "error"
                    test_results["details"]["face_detection"][test_key]["error"] = str(e)
                    print(f"  ✗ ERROR: {str(e)}")
        
        finally:
            os.chdir(original_cwd)

def test_image_stats_comprehensive():
    """Test image statistics with all URLs."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST: Image Statistics from URLs")
    print("="*70)
    
    image_urls = load_urls("image_urls.txt")
    if not image_urls:
        test_results["skipped"].append("Image stats comprehensive (no URLs)")
        return
    
    test_results["details"]["image_stats"] = {}
    
    for i, url in enumerate(image_urls, 1):
        print(f"\n[{i}/{len(image_urls)}] Testing: {url[:70]}...")
        test_key = f"url_{i}"
        test_results["details"]["image_stats"][test_key] = {"url": url, "status": "unknown"}
        
        try:
            result = image_basics.get_image_stats_tool(url, channels=True)
            
            assert "info" in result, "Missing 'info'"
            assert "min" in result and "max" in result and "mean" in result, "Missing statistics"
            assert "image_base64" in result, "Missing 'image_base64' (required for LLM access)"
            
            # Verify base64 output (PRIMARY)
            base64_str = result["image_base64"]
            is_valid_base64, base64_issues = verify_base64_image(base64_str)
            if not is_valid_base64:
                test_results["failed"].append(f"Image stats URL {i}: Base64 verification failed: {', '.join(base64_issues)}")
                test_results["details"]["image_stats"][test_key]["status"] = "failed"
                test_results["details"]["image_stats"][test_key]["error"] = f"Base64: {', '.join(base64_issues)}"
                print(f"  ✗ FAILED: Base64 verification failed: {', '.join(base64_issues)}")
                continue
            
            info = result["info"]
            assert info["width"] > 0 and info["height"] > 0, "Invalid dimensions"
            assert 0 <= result["min"] <= 255 and 0 <= result["max"] <= 255, "Invalid value range"
            assert result["min"] <= result["mean"] <= result["max"], "Mean out of range"
            
            test_results["passed"].append(f"Image stats URL {i}: {info['width']}x{info['height']} (with base64)")
            test_results["details"]["image_stats"][test_key]["status"] = "passed"
            test_results["details"]["image_stats"][test_key]["dimensions"] = f"{info['width']}x{info['height']}"
            test_results["details"]["image_stats"][test_key]["base64_length"] = len(base64_str)
            test_results["details"]["image_stats"][test_key]["channels"] = info["channels"]
            test_results["details"]["image_stats"][test_key]["mean"] = result["mean"]
            print(f"  ✓ PASSED: {info['width']}x{info['height']}, mean={result['mean']:.2f}, base64: {len(base64_str)} chars")
            
        except Exception as e:
            test_results["failed"].append(f"Image stats URL {i}: {str(e)}")
            test_results["details"]["image_stats"][test_key]["status"] = "error"
            test_results["details"]["image_stats"][test_key]["error"] = str(e)
            print(f"  ✗ ERROR: {str(e)}")

def print_summary():
    """Print comprehensive test summary."""
    print("\n" + "="*70)
    print("COMPREHENSIVE TEST SUMMARY")
    print("="*70)
    print(f"Passed: {len(test_results['passed'])}")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Skipped: {len(test_results['skipped'])}")
    print(f"Total: {len(test_results['passed']) + len(test_results['failed']) + len(test_results['skipped'])}")
    
    if test_results['passed']:
        print("\n✓ Passed Tests:")
        for test in test_results['passed'][:10]:  # Show first 10
            print(f"  ✓ {test}")
        if len(test_results['passed']) > 10:
            print(f"  ... and {len(test_results['passed']) - 10} more")
    
    if test_results['failed']:
        print("\n✗ Failed Tests:")
        for test in test_results['failed']:
            print(f"  ✗ {test}")
    
    # Save detailed results
    results_file = Path(__file__).parent / "test_comprehensive_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {results_file}")

def main():
    """Run all comprehensive tests."""
    print("="*70)
    print("OpenCV MCP Server - Comprehensive Functional Tests")
    print("="*70)
    print("Testing all URLs from image_urls.txt")
    print("Verifying actual output files and their correctness")
    print("="*70)
    
    test_resize_comprehensive()
    test_edge_detection_comprehensive()
    test_face_detection_comprehensive()
    test_image_stats_comprehensive()
    
    print_summary()
    
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

