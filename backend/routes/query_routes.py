from fastapi import APIRouter, HTTPException
from models.schemas import Query, ErrorResponse
from services.ai_service import ai_service
from services.ifc_service import ifc_service
from utils.error_handling import FileNotFoundError, AIError, handle_app_exception

router = APIRouter(
    prefix="/query",
    tags=["query"],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)

@router.post("")
async def process_query(query: Query):
    """Process a query about an IFC file"""
    try:
        if not query.file_path:
            raise HTTPException(status_code=400, detail="No file path provided")
        
        # Check if the file exists
        if not ifc_service.load_file(query.file_path):
            raise FileNotFoundError(f"File not found: {query.file_path}")
        
        # Process the query
        result = ai_service.process_query(query.message, query.file_path)
        return {"response": result}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except AIError as e:
        return handle_app_exception(None, e)
    except Exception as e:
        return handle_app_exception(None, AIError(f"Error processing query: {str(e)}")) 