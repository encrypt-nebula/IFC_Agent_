import time
import ifcopenshell
import google.generativeai as genai
import traceback
import re
import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from typing import Optional, List
from datetime import datetime

# Configuration
GENAI_API_KEY = "AIzaSyBLuL_Nw20rrNOkKo07gNERvwfXV87Kz0Y"  # Replace with your Gemini API key
MODEL_NAME = "gemini-1.5-pro-latest"  # Use a supported model name
MAX_RETRIES = 3  # Maximum code correction attempts
RETRY_DELAY = 5  # Delay in seconds between retries for quota issues
UPLOAD_DIR = "uploads"  # Directory to store uploaded files
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB max file size

# Initialize FastAPI app
app = FastAPI(
    title="IFC Chat API",
    description="API for processing IFC files and answering questions about them",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React app's address
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini model
try:
    genai.configure(api_key=GENAI_API_KEY)
    model = genai.GenerativeModel(MODEL_NAME)
    print("Gemini model initialized successfully")
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    model = None

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

class Query(BaseModel):
    message: str
    file_path: Optional[str] = None

class FileInfo(BaseModel):
    filename: str
    file_path: str
    upload_time: str
    file_size: int

# Store information about uploaded files
uploaded_files = {}

def generate_code(prompt: str) -> str:
    """Generate Python code using Gemini"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating code: {str(e)}"

def clean_code(code_text: str) -> str:
    """Clean the code by removing markdown code block delimiters and other formatting"""
    # Remove markdown code blocks (```python ... ```)
    code_text = re.sub(r'```python\s*', '', code_text)
    code_text = re.sub(r'```\s*', '', code_text)
    
    # Extract only the first code block if there are example usages
    # This prevents duplicate code execution
    if "# Example Usage:" in code_text:
        code_text = code_text.split("# Example Usage:")[0]
    
    # Remove any line that attempts to redefine ifc_file 
    code_text = re.sub(r'ifc_file\s*=\s*ifcopenshell\.open\(.*\)', '# ifc_file is already loaded', code_text)
    
    # Remove any line that tries to execute external files
    code_text = re.sub(r'exec\s*\(.*\)', '# External execution not allowed', code_text)
    
    # Remove any leading or trailing whitespace
    code_text = code_text.strip()
    
    return code_text

def format_response(result):
    """Format the result into a natural language response"""
    # Handle None results
    if result is None:
        return "I couldn't find the requested information in this IFC model. It's possible that this data isn't included in the file or is stored using different properties or entities."
    
    # Handle empty collections
    if isinstance(result, (list, dict)) and len(result) == 0:
        return "I looked through the IFC model but couldn't find any relevant data for your query. This information might not be present in the model."
    
    # Handle string results that might be error messages
    if isinstance(result, str) and result.lower() == "none":
        return "I searched the IFC model but couldn't find the requested information. This property might be missing or stored differently in this particular model."
        
    # Return the result as is for other cases
    return result

def execute_code(code: str, ifc_file) -> str:
    """Execute the generated code in a safe environment"""
    try:
        # Create isolated namespace with allowed variables
        exec_namespace = {
            'ifc_file': ifc_file,
            'ifcopenshell': ifcopenshell,
            'result': None
        }
        
        # Execute the code
        exec(code, exec_namespace)
        result = exec_namespace.get('result')
        
        # Format the result to provide natural language responses
        return format_response(result)
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Execution failed with error:\n{error_trace}")
        return f"I encountered an error while processing your query: {str(e)}"

def process_ifc_file(ifc_file_path, query):
    """Process the IFC file based on the user query"""
    try:
        ifc_file = ifcopenshell.open(ifc_file_path)

        prompt = f"""
You are an expert Python developer specializing in IFC (Industry Foundation Classes) file analysis using the ifcopenshell library.

You have access to a preloaded variable `ifc_file`, which is an ifcopenshell.file object already loaded from an IFC model.

A user has asked this query:
\"\"\"{query}\"\"\"

Write complete Python code to compute the answer based solely on the IFC model data.

---

TECHNICAL GUIDELINES:
1. Use only:
    - Python standard libraries
    - The `ifcopenshell` API (e.g., `by_type`, property traversal, geometry if needed)

2. Use the pre-loaded 'ifc_file' variable (do not open the file again or modify it)
3. Store the final result in a variable named `result`
4. Never modify the original IFC file
5. Handle potential errors with try/except blocks
6. Return plain text without markdown or code block delimiters
7. Ensure the code is complete and executable
8. Do not use exec(), input(), or external scripts

IFC GUIDELINES:

For counting elements:
- When counting walls, check both `ifc_file.by_type("IfcWall")` and `ifc_file.by_type("IfcWallStandardCase")` and combine the results
- For windows, use `ifc_file.by_type("IfcWindow")`
- For doors, use `ifc_file.by_type("IfcDoor")`
- Always handle empty collections with a fallback value so you don't return None

For finding areas:
- Try to get properties through the object's relationship to property sets:
  ```python
  for rel in element.IsDefinedBy:
      if hasattr(rel, "RelatingPropertyDefinition"):
          prop_def = rel.RelatingPropertyDefinition
          if hasattr(prop_def, "HasProperties"):
              for prop in prop_def.HasProperties:
                  if prop.Name == "Area" or prop.Name == "NetArea" or prop.Name == "GrossArea":
                      if hasattr(prop, "NominalValue"):
                          return prop.NominalValue.wrappedValue
  ```
- For windows and doors, check if they have direct attributes:
  ```python
  if hasattr(element, "OverallHeight") and hasattr(element, "OverallWidth"):
      if element.OverallHeight and element.OverallWidth:
          area = element.OverallHeight.wrappedValue * element.OverallWidth.wrappedValue
  ```
- For quantity sets, check:
  ```python
  if hasattr(prop_def, "Quantities"):
      for quantity in prop_def.Quantities:
          if quantity.Name == "Area" and hasattr(quantity, "AreaValue"):
              return quantity.AreaValue
  ```

For finding elements by floor/storey:
- Use building storeys to organize elements:
  ```python
  storeys = ifc_file.by_type("IfcBuildingStorey")
  for storey in storeys:
      storey_name = storey.Name if hasattr(storey, "Name") and storey.Name else f"Level {storey.GlobalId}"
      elements = []
      for rel in storey.ContainsElements:
          elements.extend(rel.RelatedElements)
  ```

For geometric properties not directly accessible:
- First check property sets and quantities
- Then check direct attributes
- Only use geometry calculations as a last resort

DATA VALIDATION:
- Always check if properties exist before accessing them using `hasattr()`
- Use multiple approaches to find properties, as IFC files can store the same information in different ways
- Set fallback values to avoid returning None
- Format results with units when available

MOST IMPORTANTLY: Never return None as the final result. Instead:
- For counts with no results, return 0
- For properties not found, return a descriptive message
- For aggregation with no matches, return an empty structure with explanation
- For calculations, provide context with the numbers
- Include units when relevant (m², m³, etc.)

Example result structures:
- For counts: `result = {"count": 10, "type": "IfcWall"}`
- For areas: `result = {"total_area": 150.5, "unit": "m²"}`
- For errors: `result = "The requested property 'Cost' is not available in this IFC model"`
"""

        for attempt in range(MAX_RETRIES + 1):
            try:
                code = generate_code(prompt)
                if code.startswith("Error"):
                    print(f"Attempt {attempt + 1}: {code}")
                    time.sleep(RETRY_DELAY)
                    continue

                code = clean_code(code)

                print(f"\nGenerated Code (Attempt {attempt + 1}):\n{code}")

                result = execute_code(code, ifc_file)
                
                # If the result doesn't indicate an error, return it
                if not isinstance(result, str) or not any(error_term in result for error_term in ["Error", "Traceback", "exception"]):
                    return result
                else:
                    print(f"Attempt {attempt + 1}: Code execution failed.")
                    if attempt < MAX_RETRIES:
                        # Provide better guidance for the next attempt based on the error
                        prompt += f"\n\nThe previous code failed. Error: {result}\n\nPlease fix the issues and try again with more robust error handling. Remember to always check if properties exist before accessing them and provide meaningful results even when data isn't found."
                        time.sleep(RETRY_DELAY)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    return f"I wasn't able to analyze this aspect of the IFC model after several attempts. The specific error was: {e}"

        # If all attempts fail, provide a helpful response
        return "I'm having trouble analyzing this aspect of the IFC model. The data might be structured in an unusual way or might not be present in the file."

    except Exception as e:
        print(f"Error processing IFC file: {e}")
        traceback.print_exc()
        return f"There was a problem processing the IFC file: {e}"


def cleanup_old_files():
    """Clean up files older than 24 hours"""
    try:
        current_time = datetime.now()
        for filename, file_info in list(uploaded_files.items()):
            upload_time = datetime.fromisoformat(file_info['upload_time'])
            if (current_time - upload_time).total_seconds() > 86400:  # 24 hours
                file_path = file_info['file_path']
                if os.path.exists(file_path):
                    os.remove(file_path)
                del uploaded_files[filename]
                print(f"Cleaned up old file: {filename}")
    except Exception as e:
        print(f"Error cleaning up old files: {e}")

@app.get("/")
async def root():
    """Root endpoint to check if the API is running"""
    return {"status": "ok", "message": "IFC Chat API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "model_initialized": model is not None}

@app.get("/files")
async def list_files():
    """List all uploaded files"""
    cleanup_old_files()  # Clean up old files before listing
    return {"files": list(uploaded_files.values())}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """Upload an IFC file"""
    try:
        if not file.filename.endswith('.ifc'):
            raise HTTPException(status_code=400, detail="Only .ifc files are allowed")
        
        # Check file size
        file_size = 0
        chunk_size = 1024 * 1024  # 1MB chunks
        
        # Read the file in chunks to check size
        content = await file.read()
        file_size = len(content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)}MB")
        
        # Create a unique filename to avoid conflicts
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, safe_filename)
        
        # Save the file
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Store file information
        file_info = {
            "filename": file.filename,
            "file_path": file_path,
            "upload_time": datetime.now().isoformat(),
            "file_size": file_size
        }
        uploaded_files[file.filename] = file_info
        
        # Schedule cleanup of old files
        if background_tasks:
            background_tasks.add_task(cleanup_old_files)
        
        return {"filename": file.filename, "file_path": file_path}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error uploading file: {str(e)}"}
        )

@app.post("/query")
async def process_query(query: Query):
    """Process a query about an IFC file"""
    try:
        if not query.file_path:
            raise HTTPException(status_code=400, detail="No file path provided")
        
        if not model:
            raise HTTPException(status_code=500, detail="AI model not initialized")
        
        if not os.path.exists(query.file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        result = process_ifc_file(query.file_path, query.message)
        return {"response": result}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error processing query: {str(e)}"}
        )

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file"""
    try:
        if filename not in uploaded_files:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_info = uploaded_files[filename]
        file_path = file_info['file_path']
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        del uploaded_files[filename]
        return {"message": f"File {filename} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error deleting file: {str(e)}"}
        )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"An unexpected error occurred: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)