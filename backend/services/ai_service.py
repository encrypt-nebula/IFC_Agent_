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

        # Initialize error context for feedback loop
        error_context = []
        
        prompt = f"""
        You are an expert in the Industry Foundation Classes (IFC) schema and a skilled Python developer using the ifcopenshell library. Generate clean, safe, and effective Python code to extract insights from an IFC model. You must follow the constraints below while leveraging deep IFC knowledge.

        - You *must* only return the asked output , Not extra information. 
        
        GENERAL INSTRUCTIONS:
        - The ifc_file variable is already initialized and loaded. *DO NOT reopen or redefine it*.
        - *Never modify the IFC file.* This is read-only analysis.
        - All output must be stored in a variable named result and be plain text (no markdown, no backticks, no code blocks).
        - Use only ifcopenshell, ifcopenshell.util.element, and standard libraries. No external packages.
        - Avoid exec() or eval() at all times.

        IFC OBJECTS & TYPES:
        - Walls → ifc_file.by_type("IfcWall") or "IfcWallStandardCase"
        - Spaces (Rooms) → ifc_file.by_type("IfcSpace")
        - Floors → ifc_file.by_type("IfcSlab")
        - Windows → ifc_file.by_type("IfcWindow")
        - Doors → ifc_file.by_type("IfcDoor")
        - Quantities → typically in IfcElementQuantity or psets with keys like Area, Length, Height, Width

        COMMON PROPERTY SET ACCESS:
        Use:
        python
        import ifcopenshell.util.element as util
        psets = util.get_psets(element)

        DIMENSION HANDLING:
        - If OverallWidth or OverallHeight is missing (None or not present), try extracting dimensions from the element's Name using regex.
        - Use this utility inside try/except:
        python
        import re

        def extract_dimensions_from_name(name):
            try:
                match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', name)
                if match:
                    return match.group(1), match.group(2)
            except: pass

        IFC ELEMENT SUMMARY:
        The model contains:
        - walls (e.g., "Basic Wall:UNIT-B (CA) Brick Wall-260mm_40mm One Side Plastering")
        - doors (e.g., "M_Door-Passage-Uneven-Flush:FL4 Unit-A Main Door 1640 x 2400mm")
        - windows (e.g., "Window-1:1980 x 1385mm")
        - storeys ("Level 0", "Level 1")
        - slabs (e.g., "Floor:FL4 UNIT-A Utility FF 30mm")
        - columns (e.g., "M_Concrete-Rectangular-Column:200 x 750mm")
        - beams (e.g., "M_Concrete-Rectangular Beam:200 x 600mm")

        
        Query: {query}

        
        """

        if error_context:
            prompt += "\n\nPrevious errors to handle:\n"
            for error in error_context:
                prompt += f"- {error}\n"

        # Generate and execute code with retries
        for attempt in range(MAX_RETRIES + 1):
            try:
                code = self.generate_code(prompt)
                if code.startswith("Error"):
                    print(f"Attempt {attempt + 1}: {code}")
                    error_context.append(f"Generation error: {code}")
                    time.sleep(RETRY_DELAY)
                    continue

                code = clean_code(code)
                print(f"\nGenerated Code (Attempt {attempt + 1}):\n{code}")

                ifc_file = ifc_service.load_file(ifc_file_path)
                result = execute_code(code, ifc_file)

                if "Error" not in result and "Traceback" not in result:
                    return result  # Success
                else:
                    print(f"Attempt {attempt + 1}: Code execution failed.")
                    error_msg = result.split('\n')[-1] if '\n' in result else result
                    error_context.append(f"Execution error: {error_msg}")
                    
                    if attempt < MAX_RETRIES:
                        # Enhanced error feedback for next attempt
                        prompt += "\n\nPrevious attempt failed. Here's what to fix:\n"
                        prompt += f"- Error: {error_msg}\n"
                        prompt += "- Ensure ALL operations are wrapped in try/except blocks\n"
                        prompt += "- Add fallback values for missing data\n"
                        prompt += "- Validate all properties before access\n"
                        prompt += "- Consider alternative ways to find the requested information\n"
                        time.sleep(RETRY_DELAY)
                    elif attempt >= MAX_RETRIES:
                        return f"After several attempts, I couldn't process this query successfully. Here are the errors encountered:\n" + \
                               "\n".join([f"- {err}" for err in error_context]) + \
                               "\n\nPlease try rephrasing your query or provide more specific details about what you're looking for."

            except Exception as e:
                error_context.append(f"System error: {str(e)}")
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    print(f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
                else:
                    error_summary = "\n".join([f"- {err}" for err in error_context])
                    raise AIError(f"Failed after {MAX_RETRIES} attempts. Error summary:\n{error_summary}")


# Create a singleton instance
ai_service = AIService()