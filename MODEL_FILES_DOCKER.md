# Model Files in Docker Image

## Overview

All model files from `OPENCV_DNN_MODELS_DIR` are included in the Docker image and accessible to all tools via the `OPENCV_DNN_MODELS_DIR` environment variable.

## Model Files Included

### Face Detection Models

1. **haarcascade_frontalface_default.xml** (0.89 MB)
   - Used by: `detect_faces_tool` with `method='haar'`
   - Path: `/app/OPENCV_DNN_MODELS_DIR/haarcascade_frontalface_default.xml`

2. **deploy.prototxt** (0.03 MB)
   - Used by: `detect_faces_tool` with `method='dnn'`
   - Path: `/app/OPENCV_DNN_MODELS_DIR/deploy.prototxt`

3. **res10_300x300_ssd_iter_140000.caffemodel** (10.17 MB)
   - Used by: `detect_faces_tool` with `method='dnn'`
   - Path: `/app/OPENCV_DNN_MODELS_DIR/res10_300x300_ssd_iter_140000.caffemodel`

### Object Detection Models (YOLO)

4. **yolov3.cfg** (0.01 MB)
   - Used by: `detect_objects_tool`, `detect_video_objects_tool`, `detect_camera_objects_tool`
   - Path: `/app/OPENCV_DNN_MODELS_DIR/yolov3.cfg`

5. **coco.names** (0.00 MB)
   - Used by: All YOLO-based object detection tools
   - Path: `/app/OPENCV_DNN_MODELS_DIR/coco.names`

### Missing File

**yolov3.weights** (237 MB) - **NOT INCLUDED**
- Required for YOLO object detection
- Too large to include in Docker image
- Users can download separately if needed:
  ```bash
  wget https://pjreddie.com/media/files/yolov3.weights
  # Then mount as volume or add to image
  ```

## Code Path Configuration

All tools now use `OPENCV_DNN_MODELS_DIR` environment variable:

### Haar Cascade (Face Detection)
- Checks `/app/OPENCV_DNN_MODELS_DIR/haarcascade_frontalface_default.xml` first
- Falls back to OpenCV's default location if not found

### DNN Face Detection
- Uses `/app/OPENCV_DNN_MODELS_DIR/deploy.prototxt`
- Uses `/app/OPENCV_DNN_MODELS_DIR/res10_300x300_ssd_iter_140000.caffemodel`

### YOLO Object Detection
- Uses `/app/OPENCV_DNN_MODELS_DIR/yolov3.cfg`
- Uses `/app/OPENCV_DNN_MODELS_DIR/coco.names`
- Looks for `/app/OPENCV_DNN_MODELS_DIR/yolov3.weights` (must be downloaded)

## Docker Configuration

### Environment Variable
```dockerfile
ENV OPENCV_DNN_MODELS_DIR=/app/OPENCV_DNN_MODELS_DIR
```

### File Copy
```dockerfile
COPY OPENCV_DNN_MODELS_DIR/ ./OPENCV_DNN_MODELS_DIR/
```

## Verification

All model files are verified to:
- ✅ Exist in Docker image at `/app/OPENCV_DNN_MODELS_DIR/`
- ✅ Be accessible via environment variable
- ✅ Load successfully in tools
- ✅ Work with both Haar and DNN face detection methods

## Tools Using Models

1. **detect_faces_tool** - Uses Haar cascade or DNN models
2. **detect_objects_tool** - Uses YOLO (requires weights file)
3. **detect_video_objects_tool** - Uses YOLO (requires weights file)
4. **detect_camera_objects_tool** - Uses YOLO (requires weights file)

## Testing

To verify models are accessible:
```bash
docker run --rm opencv-mcp-server:0.1.4 \
  python3 -c "import os; print(os.listdir('/app/OPENCV_DNN_MODELS_DIR/'))"
```

All 5 model files should be listed.

