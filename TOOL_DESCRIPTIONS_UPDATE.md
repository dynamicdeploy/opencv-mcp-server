# Tool Descriptions Updated for URL Support

## Summary

Updated all tool docstrings to explicitly mention that URLs are supported. This ensures that LLMs calling the MCP server will know they can pass URLs to image processing tools.

## What Changed

All tool descriptions that previously said:
- `image_path: Path to the image file`

Now say:
- `image_path: Path to the image file or URL (supports http:// and https://)`

## Updated Tools

### Image Basics
- ✅ `save_image_tool` - Updated `path_in` parameter
- ✅ `convert_color_space_tool` - Updated `image_path` parameter
- ✅ `resize_image_tool` - Updated `image_path` parameter
- ✅ `crop_image_tool` - Updated `image_path` parameter
- ✅ `get_image_stats_tool` - Updated `image_path` parameter

### Image Processing
- ✅ `apply_filter_tool` - Updated `image_path` parameter
- ✅ `detect_edges_tool` - Updated `image_path` parameter
- ✅ `apply_threshold_tool` - Updated `image_path` parameter
- ✅ `detect_contours_tool` - Updated `image_path` parameter
- ✅ `find_shapes_tool` - Updated `image_path` parameter
- ✅ `match_template_tool` - Updated both `image_path` and `template_path` parameters

### Computer Vision
- ✅ `detect_features_tool` - Updated `image_path` parameter
- ✅ `match_features_tool` - Updated both `image1_path` and `image2_path` parameters
- ✅ `detect_faces_tool` - Updated `image_path` parameter
- ✅ `detect_objects_tool` - Updated `image_path` parameter

## How LLMs See This

When an LLM calls `list_tools()` on the MCP server, it receives tool schemas that include:
- Tool name
- Tool description (from the function docstring)
- Parameter descriptions (from the Args section of the docstring)
- Parameter types

Now, when an LLM sees a tool like `resize_image_tool`, it will see:
```
image_path: Path to the image file or URL (supports http:// and https://)
```

This makes it clear that URLs are supported!

## Example

Before:
```python
"""
Args:
    image_path: Path to the image file
"""
```

After:
```python
"""
Args:
    image_path: Path to the image file or URL (supports http:// and https://)
"""
```

## Verification

You can verify the tool descriptions are updated by:
1. Starting the MCP server
2. Calling `list_tools()` via an MCP client
3. Checking the parameter descriptions in the tool schemas

The descriptions should now explicitly mention URL support.

