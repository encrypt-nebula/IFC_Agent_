import time
import traceback
from typing import Any, Dict, Optional
from utils.security import clean_code, execute_code
from utils.error_handling import CodeExecutionError
from services.ai_service import ai_service

class CodeExecutionService:
    """Service for code generation, cleaning, and execution"""
    
    def __init__(self):
        pass
    
    def generate_and_execute(self, prompt: str, ifc_file: Any, max_retries: int = 3, retry_delay: int = 5) -> str:
        """
        Generate code from a prompt and execute it
        
        Args:
            prompt: The prompt to generate code from
            ifc_file: The IFC file object
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Returns:
            The result of the code execution
        """
        for attempt in range(max_retries + 1):
            try:
                # Generate code
                code = ai_service.generate_code(prompt)
                if code.startswith("Error"):
                    print(f"Attempt {attempt + 1}: {code}")
                    time.sleep(retry_delay)
                    continue
                
                # Clean the code
                code = clean_code(code)
                
                print(f"\nGenerated Code (Attempt {attempt + 1}):\n{code}")
                
                # Execute the code
                result = execute_code(code, ifc_file)
                if "Error" not in result and "Traceback" not in result:
                    return result  # Return the final result
                else:
                    print(f"Attempt {attempt + 1}: Code execution failed.")
                    if attempt < max_retries:
                        # Improve the prompt based on the error
                        prompt += f"\n\nPrevious code had errors: {result}\nPlease fix these issues."
                        time.sleep(retry_delay)
                
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise CodeExecutionError(f"Failed after {max_retries} attempts. Final error: {e}")
    
    def create_ifc_prompt(self, query: str) -> str:
        """
        Create a prompt for IFC file analysis
        
        Args:
            query: The user's query
            
        Returns:
            A formatted prompt for the AI model
        """
        return f"""
        You are an IFC expert Python developer. Generate code to analyze an IFC file using ifcopenshell.
        Follow these strict rules:
        1. Only use ifcopenshell and standard libraries
        2. Use the pre-loaded 'ifc_file' variable (do not open the file again or modify it)
        3. Store final results in a variable named 'result'
        4. Never modify the original IFC file
        5. Handle potential errors with try/except blocks
        6. Return plain text without markdown or code block delimiters
        7. Ensure the code is complete and executable
        8. DO NOT include any backticks (```) in your response
        9. DO NOT attempt to redefine the ifc_file variable
        10. DO NOT use exec() or similar functions
        
        Important IFC Knowledge:
        - Use ifcopenshell's built-in methods like ifc_file.by_type(), ifc_file.get_entity_by_guid()
        - To get property sets, use ifcopenshell.util.element.get_psets() function on an element
        - Search for properties in psets (property sets) for cost/price information
        - In IFC, pricing can be stored in various ways: in Pset_CostItem, or custom psets with properties like "Cost", "Price", etc.
        - For buildings or units, look at property sets associated with IfcBuilding, IfcBuildingStorey, or IfcSpace elements
        
        Query: {query}
        """

# Create a singleton instance
code_execution_service = CodeExecutionService() 