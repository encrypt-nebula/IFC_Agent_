from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional

class AppException(Exception):
    """Base exception class for the application"""
    def __init__(self, message: str, status_code: int = 500, detail: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

class FileUploadError(AppException):
    """Exception for file upload errors"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=400, detail=detail)

class FileNotFoundError(AppException):
    """Exception for file not found errors"""
    def __init__(self, message: str = "File not found", detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=404, detail=detail)

class AIError(AppException):
    """Exception for AI-related errors"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)

class CodeExecutionError(AppException):
    """Exception for code execution errors"""
    def __init__(self, message: str, detail: Optional[Dict[str, Any]] = None):
        super().__init__(message, status_code=500, detail=detail)

def handle_app_exception(request: Any, exc: AppException) -> JSONResponse:
    """Handle application exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message, "additional_info": exc.detail}
    )

def handle_http_exception(request: Any, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

def handle_generic_exception(request: Any, exc: Exception) -> JSONResponse:
    """Handle generic exceptions"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"}
    ) 