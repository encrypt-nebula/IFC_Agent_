import time
import google.generativeai as genai
from config import GENAI_API_KEY, MODEL_NAME, MAX_RETRIES, RETRY_DELAY
from utils.error_handling import AIError

class AIService:
    """Service for AI integration and prompt management"""
    
    def __init__(self):
        self.model = None
        self.initialized = False
    
    def initialize(self):
        """Initialize the AI model"""
        try:
            genai.configure(api_key=GENAI_API_KEY)
            self.model = genai.GenerativeModel(MODEL_NAME)
            self.initialized = True
            print("Gemini model initialized successfully")
        except Exception as e:
            print(f"Error initializing Gemini model: {e}")
            self.initialized = False
            raise AIError(f"Failed to initialize AI model: {str(e)}")
    
    def generate_code(self, prompt: str) -> str:
        """Generate Python code using Gemini"""
        if not self.initialized:
            self.initialize()
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise AIError(f"Error generating code: {str(e)}")
    
    def process_query(self, query: str, ifc_file_path: str) -> str:
        """Process a query about an IFC file"""
        from services.ifc_service import IFCService
        from utils.security import clean_code, execute_code

        ifc_service = IFCService()

        prompt = f"""
        You are an IFC expert Python developer. Generate Python code to analyze an IFC file using ifcopenshell.
        Follow these strict rules:
        1. Use the pre-loaded 'ifc_file' variable (do not open the file again or modify it)
        2. Only use ifcopenshell and standard libraries
        3. Store final results in a variable named 'result'
        4. Never modify the original IFC file
        5. Handle errors with try/except blocks
        6. Return plain text without markdown or code block delimiters
        7. DO NOT use backticks (```)
        8. DO NOT redefine the ifc_file variable
        9. DO NOT use exec() or eval()

        IFC Domain Knowledge:
        - Use ifc_file.by_type("IfcWall") or IfcWallStandardCase to get walls (for plastering).
        - Use ifcopenshell.util.element.get_psets(element) to access property sets.
        - Look for surface area in psets using keys like "NetSideArea", "GrossSideArea", "Area", "Length" x "Height" (as fallback).
        - Use ifc_file.by_type("IfcSpace") for rooms and IfcSlab for floors to calculate area.
        - For spaces, check psets or element geometry for area properties like "NetFloorArea", "GrossFloorArea".

        Query: {query}
        """

        # Generate and execute code with retries
        for attempt in range(MAX_RETRIES + 1):
            try:
                code = self.generate_code(prompt)
                if code.startswith("Error"):
                    print(f"Attempt {attempt + 1}: {code}")
                    time.sleep(RETRY_DELAY)
                    continue

                code = clean_code(code)
                print(f"\nGenerated Code (Attempt {attempt + 1}):\n{code}")

                ifc_file = ifc_service.load_file(ifc_file_path)
                result = execute_code(code, ifc_file)

                if "Error" not in result and "Traceback" not in result:
                    return result  # ✅ Success
                else:
                    print(f"Attempt {attempt + 1}: Code execution failed.")
                    if attempt < MAX_RETRIES:
                        prompt += f"\n\nPrevious code had errors: {result}\nPlease fix these issues while adhering to the original constraints."
                        time.sleep(RETRY_DELAY)

            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    raise AIError(f"Failed after {MAX_RETRIES} attempts. Final error: {e}")


# Create a singleton instance
ai_service = AIService() 