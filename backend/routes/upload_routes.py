from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from models.schemas import FileInfo, FileList, SuccessResponse, ErrorResponse
from models.file_model import file_storage
from utils.storage import save_uploaded_file, delete_file
from utils.security import is_safe_filename
from utils.error_handling import FileUploadError, FileNotFoundError, handle_app_exception

router = APIRouter(
    prefix="/files",
    tags=["files"],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)

@router.get("", response_model=FileList)
async def list_files():
    """List all uploaded files"""
    try:
        # Clean up old files before listing
        file_storage.cleanup_old_files()
        return {"files": file_storage.list_files()}
    except Exception as e:
        return handle_app_exception(None, FileUploadError(f"Error listing files: {str(e)}"))

@router.post("/upload", response_model=FileInfo)
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload an IFC file"""
    try:
        # Validate file extension
        if not is_safe_filename(file.filename):
            raise FileUploadError("Only .ifc files are allowed")
        
        # Read the file content
        content = await file.read()
        
        # Save the file
        safe_filename, file_path, file_size = save_uploaded_file(content, file.filename)
        
        # Add to file storage
        file_info = file_storage.add_file(file.filename, file_path, file_size)
        
        # Schedule cleanup of old files
        if background_tasks:
            background_tasks.add_task(file_storage.cleanup_old_files)
        
        return file_info
    except ValueError as e:
        return handle_app_exception(None, FileUploadError(str(e)))
    except Exception as e:
        return handle_app_exception(None, FileUploadError(f"Error uploading file: {str(e)}"))

@router.delete("/{filename}", response_model=SuccessResponse)
async def delete_file_endpoint(filename: str):
    """Delete an uploaded file"""
    try:
        if file_storage.delete_file(filename):
            return {"message": f"File {filename} deleted successfully"}
        else:
            raise FileNotFoundError(f"File {filename} not found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    except Exception as e:
        return handle_app_exception(None, FileUploadError(f"Error deleting file: {str(e)}")) 