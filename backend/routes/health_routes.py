from fastapi import APIRouter
from models.schemas import HealthResponse
from services.ai_service import ai_service

router = APIRouter(
    prefix="/health",
    tags=["health"]
)

@router.get("", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_initialized": ai_service.initialized
    }

@router.get("/model")
async def model_status():
    """Check if the AI model is initialized"""
    if not ai_service.initialized:
        try:
            ai_service.initialize()
            return {"status": "initialized", "message": "Model initialized successfully"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to initialize model: {str(e)}"}
    else:
        return {"status": "ready", "message": "Model is already initialized"} 