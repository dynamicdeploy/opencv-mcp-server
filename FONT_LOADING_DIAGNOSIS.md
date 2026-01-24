# Font Loading Diagnosis - Docker Container

## Problem Summary

Fonts are not loading properly in the Docker container despite previous attempts to fix the issue.

## Root Cause Analysis

### Current Dockerfile State

The current Dockerfile (`python:3.11-slim` base image) installs:
- ✅ OpenCV dependencies (libglib2.0-0, libsm6, libxext6, etc.)
- ✅ GTK libraries (libgtk-3-0)
- ❌ **Missing font packages**

### Why Fonts Fail to Load

1. **Missing Font Configuration Library**
   - `fontconfig` - Manages font configuration and discovery
   - `libfontconfig1` - Fontconfig runtime library
   - Without these, the system cannot locate or configure fonts

2. **Missing Font Rendering Library**
   - `libfreetype6` - FreeType library for rendering fonts
   - OpenCV's text rendering depends on FreeType

3. **Missing Actual Font Files**
   - The slim base image doesn't include font files
   - Need at least one font family (e.g., DejaVu, Liberation, or Noto)

4. **OpenCV Font Rendering**
   - Even though `cv2.FONT_HERSHEY_SIMPLEX` is a built-in bitmap font, OpenCV still needs:
     - FreeType for proper rendering
     - Fontconfig for font discovery
     - Actual font files for fallback or custom fonts

## Current Code Usage

The code uses OpenCV's built-in fonts:
- `cv2.FONT_HERSHEY_SIMPLEX` in `computer_vision.py` (line 472)
- `cv2.FONT_HERSHEY_SIMPLEX` in `video_processing.py` (lines 1102, 1414, 1420)

These should work, but require the underlying font infrastructure.

## Required Fixes

### 1. Install Font Packages

Add to Dockerfile:
```dockerfile
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1 \
    libgtk-3-0 \
    wget \
    fontconfig \
    libfontconfig1 \
    libfreetype6 \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*
```

### 2. Verify Font Configuration

After installation, verify fonts are available:
```bash
docker run --rm <image> fc-list
```

Should show available fonts.

### 3. Test OpenCV Font Rendering

Test that OpenCV can render text:
```python
import cv2
import numpy as np

img = np.zeros((100, 300, 3), dtype=np.uint8)
cv2.putText(img, "Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
cv2.imwrite("/tmp/test.png", img)
```

## Common Issues After Fix

### Issue 1: Fonts Still Not Found
- **Cause**: Font cache not updated
- **Fix**: Run `fc-cache -fv` after installing fonts

### Issue 2: Permission Errors
- **Cause**: Font directories not accessible
- **Fix**: Ensure proper permissions on `/usr/share/fonts`

### Issue 3: OpenCV Still Can't Render
- **Cause**: OpenCV compiled without FreeType support
- **Fix**: Verify OpenCV build includes FreeType (check with `cv2.getBuildInformation()`)

## Verification Steps

1. **Check font packages are installed:**
   ```bash
   docker run --rm <image> dpkg -l | grep -E "fontconfig|freetype|dejavu"
   ```

2. **List available fonts:**
   ```bash
   docker run --rm <image> fc-list
   ```

3. **Test OpenCV font rendering:**
   ```bash
   docker run --rm -v $(pwd):/output <image> python -c "
   import cv2
   import numpy as np
   img = np.zeros((100, 300, 3), dtype=np.uint8)
   cv2.putText(img, 'Test', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
   cv2.imwrite('/output/test_font.png', img)
   print('Font test successful')
   "
   ```

4. **Check OpenCV build info:**
   ```bash
   docker run --rm <image> python -c "import cv2; print(cv2.getBuildInformation())" | grep -i freetype
   ```

## Expected Outcome

After applying fixes:
- ✅ Fontconfig is installed and configured
- ✅ FreeType library is available
- ✅ At least one font family (DejaVu) is installed
- ✅ OpenCV can render text using `cv2.putText()`
- ✅ No font-related errors in container logs

