#!/usr/bin/env python3
"""
Abstract base class for dNBR analyses.
Defines the interface that all analysis types must implement.
"""

from abc import ABC, abstractmethod
from ulid import ULID


class DNBRAnalysis(ABC):
    """Abstract base class for dNBR analyses."""
    
    def __init__(self):
        """Initialize analysis with a ULID."""
        self._id = str(ULID())
    
    def get_id(self) -> str:
        """Get the analysis ID."""
        return self._id
    
    @abstractmethod
    def status(self) -> str:
        """Get analysis status: PENDING, RUNNING, COMPLETED, FAILED."""
        pass
    
    @abstractmethod
    def get(self) -> bytes:
        """Get the actual raster data."""
        pass 