import re
import traceback
from typing import Dict, Any

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

def execute_code(code: str, ifc_file: Any) -> str:
    """Execute the generated code in a safe environment"""
    try:
        # Create isolated namespace with allowed variables
        exec_namespace = {
            'ifc_file': ifc_file,
            'ifcopenshell': __import__('ifcopenshell'),
            'result': None
        }
        
        # Execute the code
        exec(code, exec_namespace)
        return str(exec_namespace.get('result', 'No result returned'))
        
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Execution failed with error:\n{error_trace}")
        return error_trace

def is_safe_filename(filename: str) -> bool:
    """Check if a filename is safe to use"""
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for allowed file extension
    if not filename.endswith('.ifc'):
        return False
    
    return True 