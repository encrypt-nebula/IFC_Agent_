import os
import shutil
from datetime import datetime
from typing import Optional, Tuple
from config import UPLOAD_DIR, MAX_FILE_SIZE

def save_uploaded_file(file_content: bytes, original_filename: str) -> Tuple[str, str, int]:
    """
    Save an uploaded file to the uploads directory
    
    Args:
        file_content: The binary content of the file
        original_filename: The original filename
        
    Returns:
        Tuple of (safe_filename, file_path, file_size)
    """
    # Check file size
    file_size = len(file_content)
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB")
    
    # Create a unique filename to avoid conflicts
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{original_filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    # Save the file
    with open(file_path, "wb") as buffer:
        buffer.write(file_content)
    
    return safe_filename, file_path, file_size

def delete_file(file_path: str) -> bool:
    """
    Delete a file from the filesystem
    
    Args:
        file_path: The path to the file
        
    Returns:
        True if the file was deleted, False otherwise
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception as e:
        print(f"Error deleting file: {e}")
        return False

def get_file_info(file_path: str) -> Optional[dict]:
    """
    Get information about a file
    
    Args:
        file_path: The path to the file
        
    Returns:
        Dictionary with file information or None if the file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        return {
            "filename": file_name,
            "file_path": file_path,
            "file_size": file_size
        }
    except Exception as e:
        print(f"Error getting file info: {e}")
        return None 