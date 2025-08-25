#!/usr/bin/env python3
"""
Abstract base class for dNBR analyses.
Defines the interface that all analysis types must implement.
"""

from ulid import ULID
import json
from typing import List


class DNBRAnalysis:
    """Concrete base class for dNBR analyses."""
    
    def __init__(self):
        """Initialize analysis with a ULID."""
        self._id = str(ULID())
        self._raster_urls: List[str] = []
    
    def get_id(self) -> str:
        """Get the analysis ID."""
        return self._id
    
    @property
    def status(self) -> str:
        """Get analysis status: PENDING, RUNNING, COMPLETED, FAILED."""
        return self._get_status()
    
    @property
    def raster_urls(self) -> List[str]:
        """Get list of raster URLs for this analysis."""
        return self._raster_urls.copy()
    
    def _get_status(self) -> str:
        """Get analysis status: PENDING, RUNNING, COMPLETED, FAILED."""
        return "PENDING"
    
    def get(self) -> bytes:
        """Get the actual raster data."""
        raise NotImplementedError("Subclasses must implement get() method")
    
    def to_json(self) -> str:
        """Convert analysis metadata to JSON string."""
        data = {
            'id': self._id,
            'status': self.status,
            'raster_urls': self.raster_urls
        }
        return json.dumps(data, indent=2) 