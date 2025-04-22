from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class Query(BaseModel):
    """Schema for query requests"""
    message: str
    file_path: Optional[str] = None

class FileInfo(BaseModel):
    """Schema for file information"""
    filename: str
    file_path: str
    upload_time: str
    file_size: int

class FileList(BaseModel):
    """Schema for file list response"""
    files: List[FileInfo]

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    model_initialized: bool

class ErrorResponse(BaseModel):
    """Schema for error responses"""
    detail: str

class SuccessResponse(BaseModel):
    """Schema for success responses"""
    message: str 