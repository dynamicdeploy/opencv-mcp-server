# URL Support in OpenCV MCP Server

## Overview

**There is no separate "download tool"** - URL support is built into **all image processing tools** automatically!

When you pass a URL to any tool that accepts an `image_path` parameter, the server automatically:
1. Detects it's a URL
2. Downloads the image to a temporary file
3. Processes it as if it were a local file

## How It Works

The URL downloading is handled by the `read_image()` utility function in `utils.py`:

- **`is_url(path: str)`** - Detects if a path is a URL (HTTP/HTTPS)
- **`download_image_from_url(url: str)`** - Downloads the image from URL to a temporary file
- **`read_image(image_path_or_url: str)`** - Automatically handles both local paths and URLs

All tools that use `read_image()` automatically support URLs!

## All Tools That Support URLs

### Image Basics (6 tools)
✅ **`get_image_stats_tool`** - Get image statistics  
✅ **`resize_image_tool`** - Resize images  
✅ **`crop_image_tool`** - Crop images  
✅ **`rotate_image_tool`** - Rotate images  
✅ **`flip_image_tool`** - Flip images  
✅ **`convert_color_space_tool`** - Convert color spaces  
✅ **`save_image_tool`** - Save images  

### Image Processing (7 tools)
✅ **`detect_edges_tool`** - Detect edges (Canny, Sobel, Laplacian)  
✅ **`apply_filter_tool`** - Apply filters (blur, sharpen, etc.)  
✅ **`adjust_brightness_contrast_tool`** - Adjust brightness/contrast  
✅ **`apply_threshold_tool`** - Apply thresholding  
✅ **`detect_contours_tool`** - Find contours  
✅ **`find_shapes_tool`** - Find shapes  
✅ **`match_template_tool`** - Template matching (both source and template can be URLs)  

### Computer Vision (4 tools)
✅ **`detect_faces_tool`** - Detect faces (Haar, DNN)  
✅ **`detect_objects_tool`** - Detect objects (YOLO)  
✅ **`detect_features_tool`** - Detect features (SIFT, ORB, etc.)  
✅ **`match_features_tool`** - Match features (both images can be URLs)  

### Video Processing (5 tools)
✅ **`extract_video_frames_tool`** - Extract frames (video can be URL)  
✅ **`process_video_tool`** - Process video (video can be URL)  
✅ **`detect_motion_tool`** - Detect motion (frames can be URLs)  
✅ **`track_object_tool`** - Track objects  
✅ **`detect_video_objects_tool`** - Detect objects in video (video can be URL)  

## Usage Examples

### Example 1: Resize Image from URL
```json
{
  "name": "resize_image_tool",
  "arguments": {
    "image_path": "https://example.com/image.jpg",
    "width": 800,
    "height": 600
  }
}
```

### Example 2: Detect Faces from URL
```json
{
  "name": "detect_faces_tool",
  "arguments": {
    "image_path": "https://example.com/photo.jpg",
    "method": "haar"
  }
}
```

### Example 3: Get Image Statistics from URL
```json
{
  "name": "get_image_stats_tool",
  "arguments": {
    "image_path": "https://jvns.ca/images/flct.png",
    "channels": true
  }
}
```

### Example 4: Template Matching (Both URLs)
```json
{
  "name": "match_template_tool",
  "arguments": {
    "image_path": "https://example.com/source.jpg",
    "template_path": "https://example.com/template.jpg",
    "method": "TM_CCOEFF_NORMED"
  }
}
```

## Supported URL Formats

- ✅ **HTTPS URLs:** `https://example.com/image.jpg`
- ✅ **HTTP URLs:** `http://example.com/image.png`
- ❌ **file:// URLs:** Not supported (use local paths instead)

## Supported Image Formats

The downloader automatically detects image format from:
- Content-Type header
- URL file extension
- Falls back to `.jpg` if unknown

Supported formats:
- JPEG/JPG
- PNG
- GIF
- WebP
- Other formats supported by OpenCV

## Technical Details

### Download Process

1. **URL Detection:** `is_url()` checks if the path starts with `http://` or `https://`
2. **Download:** `download_image_from_url()` uses the `requests` library to download
3. **Temporary Storage:** Image is saved to a temporary file
4. **Processing:** OpenCV reads the temporary file
5. **Cleanup:** Temporary file is cleaned up automatically

### Error Handling

- Network errors are caught and reported
- Invalid URLs raise `ValueError`
- Download timeouts default to 30 seconds
- Failed downloads provide clear error messages

## Requirements

- **`requests` library** must be installed (included in dependencies)
- **Network connectivity** for downloading from URLs
- **Valid image URLs** that return image data

## Summary

**All 22 image processing tools support URLs automatically!** Just pass a URL instead of a file path to any tool's `image_path` parameter, and the server will handle downloading and processing seamlessly.

