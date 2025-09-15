# Placeholder for CortexXSIAMBackend - will be replaced when user uploads the actual backend
from sigma.rule import SigmaRule
from typing import List, Union

class CortexXSIAMBackend:
    """Placeholder CortexXSIAMBackend class"""
    
    def __init__(self, processing_pipeline=None):
        self.processing_pipeline = processing_pipeline
    
    def convert_rule(self, rule: SigmaRule) -> Union[str, List[str]]:
        """Placeholder conversion method"""
        return ["# Placeholder query - backend will be replaced when user uploads the actual files"]