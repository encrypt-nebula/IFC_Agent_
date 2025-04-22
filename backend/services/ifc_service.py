import ifcopenshell
from utils.error_handling import FileNotFoundError

class IFCService:
    """Service for IFC file processing"""
    
    def __init__(self):
        pass
    
    def load_file(self, file_path: str):
        """Load an IFC file"""
        try:
            return ifcopenshell.open(file_path)
        except Exception as e:
            raise FileNotFoundError(f"Error loading IFC file: {str(e)}")
    
    def get_file_info(self, ifc_file):
        """Get basic information about an IFC file"""
        try:
            # Get the schema version
            schema = ifc_file.schema
            
            # Get the project name
            project = ifc_file.by_type("IfcProject")[0]
            project_name = project.Name if hasattr(project, "Name") else "Unnamed Project"
            
            # Get the number of elements by type
            element_counts = {}
            for element_type in ifc_file.by_type():
                type_name = element_type.is_a()
                element_counts[type_name] = element_counts.get(type_name, 0) + 1
            
            return {
                "schema": schema,
                "project_name": project_name,
                "element_counts": element_counts
            }
        except Exception as e:
            return {"error": f"Error getting file info: {str(e)}"}
    
    def get_property_sets(self, ifc_file, entity):
        """Get property sets for an entity"""
        try:
            import ifcopenshell.util.element as element_util
            return element_util.get_psets(entity)
        except ImportError:
            # Fallback if the utility module is not available
            psets = {}
            for rel in entity.IsDefinedBy:
                if rel.is_a("IfcRelDefinesByProperties"):
                    for prop_set in rel.RelatingPropertyDefinition:
                        if prop_set.is_a("IfcPropertySet"):
                            psets[prop_set.Name] = {}
                            for prop in prop_set.HasProperties:
                                if prop.is_a("IfcPropertySingleValue"):
                                    psets[prop_set.Name][prop.Name] = prop.NominalValue.wrappedValue
            return psets
        except Exception as e:
            return {"error": f"Error getting property sets: {str(e)}"}

# Create a singleton instance
ifc_service = IFCService() 