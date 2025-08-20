#!/usr/bin/env python3
"""
Dummy analysis implementation for testing and development.
"""

import os
from .analysis import DNBRAnalysis


class DummyAnalysis(DNBRAnalysis):
    """Dummy analysis that completes immediately and contains data from file."""
    
    def __init__(self):
        super().__init__()
        self._result_path = "data/dummy/fire_severity.tif"
    
    def status(self) -> str:
        """Dummy analyses are always completed."""
        return "COMPLETED"
    
    def get(self) -> bytes:
        """Get dummy raster data from file."""
        if not os.path.exists(self._result_path):
            raise FileNotFoundError(f"Dummy raster not found: {self._result_path}")
        with open(self._result_path, 'rb') as f:
            return f.read() 