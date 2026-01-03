#!/usr/bin/env python3
"""
Test script for OpenCV MCP Server URL processing capabilities.

This script tests various image processing operations using URLs from
image_urls.txt and verifies that URL support works correctly.
"""

import os
import sys
import json
from pathlib import Path

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
    # Try multiple paths
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
        print(f"Loaded {len(urls)} URLs from {filepath}")
    else:
        print(f"Warning: File {filename} not found in any of: {[str(p) for p in possible_paths]}")
    return urls

def test_url_detection():
    """Test URL detection utility."""
    print("\n=== Testing URL Detection ===")
    test_cases = [
        ("https://example.com/image.jpg", True),
        ("http://example.com/image.png", True),
        ("/local/path/image.jpg", False),
        ("image.jpg", False),
        ("file:///local/path/image.jpg", True),
    ]
    
    for url, expected in test_cases:
        result = is_url(url)
        if result == expected:
            test_results["passed"].append(f"URL detection: {url}")
            print(f"✓ URL detection: {url} -> {result}")
        else:
            test_results["failed"].append(f"URL detection: {url} (expected {expected}, got {result})")
            print(f"✗ URL detection: {url} (expected {expected}, got {result})")

def test_image_read_from_url():
    """Test reading images from URLs."""
    print("\n=== Testing Image Read from URLs ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        print("No image URLs found in image_urls.txt")
        test_results["skipped"].append("Image read from URLs (no URLs available)")
        return
    
    # Test first few URLs
    for i, url in enumerate(image_urls[:3], 1):
        try:
            print(f"\nTesting URL {i}/{min(3, len(image_urls))}: {url[:60]}...")
            img = read_image(url)
            if img is not None and img.size > 0:
                test_results["passed"].append(f"Read image from URL: {url[:50]}...")
                print(f"✓ Successfully read image: {img.shape}")
            else:
                test_results["failed"].append(f"Read image from URL returned None or empty: {url[:50]}...")
                print(f"✗ Failed: Image is None or empty")
        except Exception as e:
            test_results["failed"].append(f"Read image from URL error: {url[:50]}... - {str(e)}")
            print(f"✗ Error: {str(e)}")

def test_resize_from_url():
    """Test resizing images from URLs."""
    print("\n=== Testing Resize from URLs ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        print("No image URLs found")
        test_results["skipped"].append("Resize from URLs (no URLs available)")
        return
    
    # Test with first URL
    url = image_urls[0]
    try:
        print(f"Testing resize with: {url[:60]}...")
        result = image_basics.resize_image_tool(
            image_path=url,
            width=400,
            height=300
        )
        if result.get("success") or result.get("path"):
            test_results["passed"].append(f"Resize from URL: {url[:50]}...")
            print(f"✓ Successfully resized image")
            print(f"  Output path: {result.get('path', 'N/A')}")
            print(f"  Dimensions: {result.get('info', {}).get('width', 'N/A')}x{result.get('info', {}).get('height', 'N/A')}")
        else:
            test_results["failed"].append(f"Resize from URL failed: {url[:50]}...")
            print(f"✗ Resize failed")
    except Exception as e:
        test_results["failed"].append(f"Resize from URL error: {url[:50]}... - {str(e)}")
        print(f"✗ Error: {str(e)}")

def test_edge_detection_from_url():
    """Test edge detection from URLs."""
    print("\n=== Testing Edge Detection from URLs ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        print("No image URLs found")
        test_results["skipped"].append("Edge detection from URLs (no URLs available)")
        return
    
    # Test with first URL
    url = image_urls[0]
    try:
        print(f"Testing edge detection with: {url[:60]}...")
        result = image_processing.detect_edges_tool(
            image_path=url,
            method="canny",
            threshold1=100,
            threshold2=200
        )
        if result.get("path"):
            test_results["passed"].append(f"Edge detection from URL: {url[:50]}...")
            print(f"✓ Successfully detected edges")
            print(f"  Output path: {result.get('path', 'N/A')}")
        else:
            test_results["failed"].append(f"Edge detection from URL failed: {url[:50]}...")
            print(f"✗ Edge detection failed")
    except Exception as e:
        test_results["failed"].append(f"Edge detection from URL error: {url[:50]}... - {str(e)}")
        print(f"✗ Error: {str(e)}")

def test_face_detection_from_url():
    """Test face detection from URLs."""
    print("\n=== Testing Face Detection from URLs ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        print("No image URLs found")
        test_results["skipped"].append("Face detection from URLs (no URLs available)")
        return
    
    # Test with first URL (preferably one with faces)
    url = image_urls[0]  # This should be the people photo
    try:
        print(f"Testing face detection with: {url[:60]}...")
        result = computer_vision.detect_faces_tool(
            image_path=url,
            method="haar",
            min_neighbors=5
        )
        if result.get("path"):
            test_results["passed"].append(f"Face detection from URL: {url[:50]}...")
            print(f"✓ Successfully detected faces")
            print(f"  Faces found: {result.get('face_count', 0)}")
            print(f"  Output path: {result.get('path', 'N/A')}")
        else:
            test_results["failed"].append(f"Face detection from URL failed: {url[:50]}...")
            print(f"✗ Face detection failed")
    except Exception as e:
        test_results["failed"].append(f"Face detection from URL error: {url[:50]}... - {str(e)}")
        print(f"✗ Error: {str(e)}")

def test_image_stats_from_url():
    """Test getting image statistics from URLs."""
    print("\n=== Testing Image Statistics from URLs ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        print("No image URLs found")
        test_results["skipped"].append("Image stats from URLs (no URLs available)")
        return
    
    # Test with first URL
    url = image_urls[0]
    try:
        print(f"Testing image stats with: {url[:60]}...")
        result = image_basics.get_image_stats_tool(
            image_path=url,
            channels=True
        )
        if result.get("info"):
            test_results["passed"].append(f"Image stats from URL: {url[:50]}...")
            print(f"✓ Successfully got image statistics")
            print(f"  Dimensions: {result.get('info', {}).get('width', 'N/A')}x{result.get('info', {}).get('height', 'N/A')}")
            print(f"  Channels: {result.get('info', {}).get('channels', 'N/A')}")
        else:
            test_results["failed"].append(f"Image stats from URL failed: {url[:50]}...")
            print(f"✗ Image stats failed")
    except Exception as e:
        test_results["failed"].append(f"Image stats from URL error: {url[:50]}... - {str(e)}")
        print(f"✗ Error: {str(e)}")

def test_filter_from_url():
    """Test applying filters to images from URLs."""
    print("\n=== Testing Filter Application from URLs ===")
    image_urls = load_urls("image_urls.txt")
    
    if not image_urls:
        print("No image URLs found")
        test_results["skipped"].append("Filter from URLs (no URLs available)")
        return
    
    # Test with first URL
    url = image_urls[0]
    try:
        print(f"Testing filter with: {url[:60]}...")
        result = image_processing.apply_filter_tool(
            image_path=url,
            filter_type="gaussian",
            kernel_size=5,
            sigma=1.5
        )
        if result.get("path"):
            test_results["passed"].append(f"Filter from URL: {url[:50]}...")
            print(f"✓ Successfully applied filter")
            print(f"  Output path: {result.get('path', 'N/A')}")
        else:
            test_results["failed"].append(f"Filter from URL failed: {url[:50]}...")
            print(f"✗ Filter failed")
    except Exception as e:
        test_results["failed"].append(f"Filter from URL error: {url[:50]}... - {str(e)}")
        print(f"✗ Error: {str(e)}")

def print_summary():
    """Print test summary."""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {len(test_results['passed'])}")
    print(f"Failed: {len(test_results['failed'])}")
    print(f"Skipped: {len(test_results['skipped'])}")
    print(f"Total: {len(test_results['passed']) + len(test_results['failed']) + len(test_results['skipped'])}")
    
    if test_results['failed']:
        print("\nFailed Tests:")
        for failure in test_results['failed']:
            print(f"  ✗ {failure}")
    
    if test_results['skipped']:
        print("\nSkipped Tests:")
        for skipped in test_results['skipped']:
            print(f"  ⊘ {skipped}")
    
    # Save results to JSON
    results_file = Path(__file__).parent / "test_results.json"
    with open(results_file, 'w') as f:
        json.dump(test_results, f, indent=2)
    print(f"\nResults saved to: {results_file}")

def main():
    """Run all tests."""
    print("="*60)
    print("OpenCV MCP Server - URL Processing Tests")
    print("="*60)
    
    # Run tests
    test_url_detection()
    test_image_read_from_url()
    test_resize_from_url()
    test_edge_detection_from_url()
    test_face_detection_from_url()
    test_image_stats_from_url()
    test_filter_from_url()
    
    # Print summary
    print_summary()
    
    # Exit with appropriate code
    if test_results['failed']:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

