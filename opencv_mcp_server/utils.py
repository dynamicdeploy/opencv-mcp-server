import cv2
import numpy as np
import os
import logging
import datetime
import subprocess
import platform
import tempfile
import urllib.parse
import base64
from typing import Optional, Dict, Any, List, Union, Tuple

logger = logging.getLogger("opencv-mcp-server.utils")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests library not available. URL support will be limited.")

# Utility Functions
def get_image_info(image: np.ndarray) -> Dict[str, Any]:
    """
    Get basic information about an image
    
    Args:
        image: OpenCV image
        
    Returns:
        Dict: Image information including dimensions, channels, etc.
    """
    if image is None:
        raise ValueError("Image is None")
    
    height, width = image.shape[:2]
    channels = 1 if len(image.shape) == 2 else image.shape[2]
    dtype = str(image.dtype)
    size_bytes = image.nbytes
    
    return {
        "width": width,
        "height": height,
        "channels": channels,
        "dtype": dtype,
        "size_bytes": size_bytes,
        "size_mb": round(size_bytes / (1024 * 1024), 2)
    }

def get_timestamp() -> str:
    """
    Get current timestamp as a string
    
    Returns:
        str: Formatted timestamp
    """
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def open_image_with_system_viewer(image_path: str) -> None:
    """
    Open an image with the system's default image viewer
    
    Args:
        image_path: Path to the image file
    """
    # Platform-specific image opening commands
    system = platform.system()
    
    try:
        if system == 'Windows':
            os.startfile(image_path)
        elif system == 'Darwin':  # macOS
            subprocess.call(['open', image_path])
        else:  # Linux and other Unix-like systems
            subprocess.call(['xdg-open', image_path])
        
        logger.info(f"Opened image: {image_path}")
    except Exception as e:
        logger.error(f"Error opening image with system viewer: {e}")
        # Continue execution even if display fails

def open_video_with_system_viewer(video_path: str) -> None:
    """
    Open a video with the system's default video player
    
    Args:
        video_path: Path to the video file
    """
    # Platform-specific video opening commands
    system = platform.system()
    
    try:
        if system == 'Windows':
            os.startfile(video_path)
        elif system == 'Darwin':  # macOS
            subprocess.call(['open', video_path])
        else:  # Linux and other Unix-like systems
            subprocess.call(['xdg-open', video_path])
        
        logger.info(f"Opened video: {video_path}")
    except Exception as e:
        logger.error(f"Error opening video with system viewer: {e}")
        # Continue execution even if display fails

def get_video_output_folder(video_path: str, operation: str) -> str:
    """
    Create and return a folder for storing video processing outputs
    
    Args:
        video_path: Path to the video file
        operation: Name of operation being performed
        
    Returns:
        str: Path to the output folder
    """
    # Get directory of original video
    directory = os.path.dirname(video_path) or '.'
    
    # Get video filename without extension
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    # Create folder name with video name, operation and timestamp
    timestamp = get_timestamp()
    folder_name = f"{video_name}_{operation}_{timestamp}"
    folder_path = os.path.join(directory, folder_name)
    
    # Create folder if it doesn't exist
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    return folder_path

def is_url(path: str) -> bool:
    """
    Check if a path is a URL
    
    Args:
        path: Path or URL to check
        
    Returns:
        bool: True if path is a URL, False otherwise
    """
    try:
        result = urllib.parse.urlparse(path)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def download_image_from_url(url: str, timeout: int = 30) -> str:
    """
    Download an image from a URL and save it to a temporary file
    
    Args:
        url: URL of the image to download
        timeout: Request timeout in seconds
        
    Returns:
        str: Path to the downloaded temporary file
    """
    if not REQUESTS_AVAILABLE:
        raise ImportError("requests library is required for URL support. Install it with: pip install requests")
    
    try:
        # Download the image
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Determine file extension from URL or Content-Type
        content_type = response.headers.get('Content-Type', '')
        ext = '.jpg'  # default
        if 'image/png' in content_type:
            ext = '.png'
        elif 'image/jpeg' in content_type or 'image/jpg' in content_type:
            ext = '.jpg'
        elif 'image/gif' in content_type:
            ext = '.gif'
        elif 'image/webp' in content_type:
            ext = '.webp'
        else:
            # Try to get extension from URL
            parsed = urllib.parse.urlparse(url)
            path_ext = os.path.splitext(parsed.path)[1]
            if path_ext:
                ext = path_ext
        
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        temp_file.write(response.content)
        temp_file.close()
        
        logger.info(f"Downloaded image from URL: {url} to {temp_file.name}")
        return temp_file.name
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Error downloading image from URL {url}: {str(e)}")
        raise ValueError(f"Failed to download image from URL: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error downloading image from URL {url}: {str(e)}")
        raise ValueError(f"Failed to download image from URL: {str(e)}")

def read_image(image_path_or_url: str) -> np.ndarray:
    """
    Read an image from a local path or URL
    
    Args:
        image_path_or_url: Local file path or URL to the image
        
    Returns:
        np.ndarray: OpenCV image array
    """
    # Check if it's a URL
    if is_url(image_path_or_url):
        # Download the image to a temporary file
        temp_path = download_image_from_url(image_path_or_url)
        try:
            # Read the image
            img = cv2.imread(temp_path)
            if img is None:
                raise ValueError(f"Failed to read downloaded image from URL: {image_path_or_url}")
            return img
        finally:
            # Clean up temporary file after reading
            # Note: We keep the file for now in case it's needed later
            # The file will be cleaned up when the process exits or tempfile cleanup runs
            pass
    else:
        # Read from local file
        img = cv2.imread(image_path_or_url)
        if img is None:
            raise ValueError(f"Failed to read image from path: {image_path_or_url}")
        return img

def save_and_display(img: np.ndarray, original_path: str, operation: str) -> str:
    """
    Save image to file and display it using system's default image viewer
    
    Args:
        img: OpenCV image
        original_path: Path to original image (can be URL or local path)
        operation: Name of operation performed
        
    Returns:
        str: Path to saved image
    """
    # Check if original_path is a URL
    if is_url(original_path):
        # For URLs, use current working directory or temp directory
        directory = os.getcwd()
        
        # Extract filename from URL
        parsed = urllib.parse.urlparse(original_path)
        url_path = parsed.path
        base_name = os.path.basename(url_path) or "image"
        
        # Remove query parameters from filename if present
        if '?' in base_name:
            base_name = base_name.split('?')[0]
        
        # If no extension, try to determine from URL or use default
        if not os.path.splitext(base_name)[1]:
            # Try to get extension from Content-Type or use .jpg as default
            ext = '.jpg'
            if '.png' in original_path.lower():
                ext = '.png'
            elif '.gif' in original_path.lower():
                ext = '.gif'
            elif '.webp' in original_path.lower():
                ext = '.webp'
            base_name = base_name + ext
    else:
        # Determine if this is a video frame by checking if the path contains specific markers
        is_video_frame = any(marker in os.path.basename(original_path) for marker in 
                             ["_frame_", "_track_", "_motion_"])
        
        # Get filename without extension
        base_name = os.path.basename(original_path)
        
        # Get directory based on whether it's a video frame or regular image
        if is_video_frame:
            # Use the same directory as the original
            directory = os.path.dirname(original_path)
        else:
            # Get directory of original image
            directory = os.path.dirname(original_path) or '.'
    
    # Get filename parts
    name_parts = os.path.splitext(base_name)
    
    # Create new filename with operation and timestamp
    timestamp = get_timestamp()
    new_filename = f"{name_parts[0]}_{operation}_{timestamp}{name_parts[1]}"
    
    new_path = os.path.join(directory, new_filename)
    
    # Ensure directory exists
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
    
    # Save image
    cv2.imwrite(new_path, img)
    
    # Verify the file was saved
    if not os.path.exists(new_path):
        raise ValueError(f"Failed to save image to {new_path}")
    
    # Display image using system's default image viewer (suppress errors in headless environments)
    try:
        open_image_with_system_viewer(new_path)
    except Exception as e:
        logger.debug(f"Could not open image viewer (this is normal in headless environments): {e}")
    
    return new_path

def encode_image_to_base64(img: np.ndarray, format: str = "jpg", quality: int = 95) -> str:
    """
    Encode an OpenCV image to base64 string
    
    Args:
        img: OpenCV image (numpy array)
        format: Image format ('jpg', 'png', 'webp')
        quality: JPEG quality (1-100, only for jpg)
        
    Returns:
        str: Base64-encoded image string (with data URI prefix)
    """
    try:
        # Determine file extension and encoding params
        if format.lower() == "jpg" or format.lower() == "jpeg":
            ext = ".jpg"
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            mime_type = "image/jpeg"
        elif format.lower() == "png":
            ext = ".png"
            encode_params = [cv2.IMWRITE_PNG_COMPRESSION, 9]
            mime_type = "image/png"
        elif format.lower() == "webp":
            ext = ".webp"
            encode_params = [cv2.IMWRITE_WEBP_QUALITY, quality]
            mime_type = "image/webp"
        else:
            # Default to JPEG
            ext = ".jpg"
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, quality]
            mime_type = "image/jpeg"
        
        # Encode image to bytes
        success, buffer = cv2.imencode(ext, img, encode_params)
        
        if not success:
            raise ValueError(f"Failed to encode image to {format}")
        
        # Convert to base64
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Return as data URI
        return f"data:{mime_type};base64,{img_base64}"
        
    except Exception as e:
        logger.error(f"Error encoding image to base64: {str(e)}")
        raise ValueError(f"Failed to encode image to base64: {str(e)}")

def save_and_encode_image(img: np.ndarray, original_path: str, operation: str, format: str = "jpg") -> Tuple[str, str]:
    """
    Save image to file and encode to base64 for return in response
    
    Args:
        img: OpenCV image
        original_path: Path to original image (can be URL or local path)
        operation: Name of operation performed
        format: Output format for base64 encoding ('jpg', 'png', 'webp')
        
    Returns:
        Tuple[str, str]: (file_path, base64_encoded_image)
    """
    # Save to file (for backward compatibility, though files are ephemeral)
    file_path = save_and_display(img, original_path, operation)
    
    # Encode to base64
    base64_data = encode_image_to_base64(img, format=format)
    
    return (file_path, base64_data)

def encode_video_to_base64(video_path: str) -> str:
    """
    Encode a video file to base64 string
    
    Args:
        video_path: Path to the video file
        
    Returns:
        str: Base64-encoded video string (with data URI prefix)
    """
    try:
        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found: {video_path}")
        
        # Read video file as binary
        with open(video_path, 'rb') as video_file:
            video_bytes = video_file.read()
        
        # Determine MIME type from file extension
        ext = os.path.splitext(video_path)[1].lower()
        mime_types = {
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm'
        }
        mime_type = mime_types.get(ext, 'video/mp4')
        
        # Encode to base64
        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
        
        # Return as data URI
        return f"data:{mime_type};base64,{video_base64}"
        
    except Exception as e:
        logger.error(f"Error encoding video to base64: {str(e)}")
        raise ValueError(f"Failed to encode video to base64: {str(e)}")
