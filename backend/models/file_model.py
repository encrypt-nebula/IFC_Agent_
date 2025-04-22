from datetime import datetime
from typing import Dict, Optional
import os
from config import UPLOAD_DIR, FILE_EXPIRY

class FileStorage:
    """Class to manage file storage and tracking"""
    
    def __init__(self):
        self.files: Dict[str, dict] = {}
    
    def add_file(self, filename: str, file_path: str, file_size: int) -> dict:
        """Add a file to the storage"""
        file_info = {
            "filename": filename,
            "file_path": file_path,
            "upload_time": datetime.now().isoformat(),
            "file_size": file_size
        }
        self.files[filename] = file_info
        return file_info
    
    def get_file(self, filename: str) -> Optional[dict]:
        """Get file information by filename"""
        return self.files.get(filename)
    
    def delete_file(self, filename: str) -> bool:
        """Delete a file from storage"""
        if filename in self.files:
            file_info = self.files[filename]
            file_path = file_info["file_path"]
            
            # Remove the file from disk if it exists
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from tracking
            del self.files[filename]
            return True
        return False
    
    def list_files(self) -> list:
        """List all files in storage"""
        return list(self.files.values())
    
    def cleanup_old_files(self) -> int:
        """Clean up files older than the expiry time"""
        current_time = datetime.now()
        files_to_delete = []
        
        # Find files to delete
        for filename, file_info in self.files.items():
            upload_time = datetime.fromisoformat(file_info["upload_time"])
            if (current_time - upload_time) > FILE_EXPIRY:
                files_to_delete.append(filename)
        
        # Delete the files
        for filename in files_to_delete:
            self.delete_file(filename)
        
        return len(files_to_delete)

# Create a singleton instance
file_storage = FileStorage() 