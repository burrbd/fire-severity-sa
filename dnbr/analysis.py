#!/usr/bin/env python3
"""
Analysis metadata and data structures for dNBR analysis results.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import ulid
from .fire_metadata import FireMetadata


class DNBRAnalysis:
    """Metadata and data for a dNBR analysis result."""
    
    def __init__(self, generator_type: str = "unknown", fire_metadata: FireMetadata = None):
        """
        Initialize a dNBR analysis.
        
        Args:
            generator_type: Type of generator used ("dummy", "gee", etc.)
            fire_metadata: Fire metadata object
        """
        self._id = str(ulid.ULID())
        self._generator_type = generator_type
        self._fire_metadata = fire_metadata
        self._status = "PENDING"
        self._created_at = datetime.utcnow().isoformat()
        self._raw_raster_url: Optional[str] = None
        self._source_vector_url: Optional[str] = None
        self._published_dnbr_raster_url: Optional[str] = None
        self._published_vector_url: Optional[str] = None
    
    @property
    def generator_type(self) -> str:
        """Get the generator type used for this analysis."""
        return self._generator_type
    
    @property
    def fire_metadata(self) -> Optional[FireMetadata]:
        """Get the fire metadata object."""
        return self._fire_metadata
    
    def get_aoi_id(self) -> Optional[str]:
        """Get the area of interest ID from fire metadata."""
        if self._fire_metadata:
            return self._fire_metadata.get_id()
        return None
    
    def get_fire_date(self) -> Optional[str]:
        """Get the fire date from the fire metadata."""
        if self._fire_metadata:
            return self._fire_metadata.get_date()
        return None
    
    def get_provider(self) -> Optional[str]:
        """Get the data provider name from the fire metadata."""
        if self._fire_metadata:
            return self._fire_metadata.get_provider()
        return None
    
    @property
    def raw_raster_url(self) -> Optional[str]:
        """Get the URL/path to the raw raster file containing dNBR results."""
        return self._raw_raster_url
    
    @property
    def published_dnbr_raster_url(self) -> Optional[str]:
        """Get the published URL to the dNBR raster COG file."""
        return self._published_dnbr_raster_url
    
    @property
    def source_vector_url(self) -> Optional[str]:
        """Get the source URL/path to the input vector GeoJSON file."""
        return self._source_vector_url
    
    @property
    def published_vector_url(self) -> Optional[str]:
        """Get the published URL to the vector GeoJSON file."""
        return self._published_vector_url
    
    def get_id(self) -> str:
        """Get the unique analysis ID."""
        return self._id
    
    def get_status(self) -> str:
        """Get the current status of the analysis."""
        return self._status
    
    @property
    def status(self) -> str:
        """Get the current status of the analysis."""
        return self._status
    
    def set_status(self, status: str) -> None:
        """Set the status of the analysis."""
        self._status = status
    
    def get_created_at(self) -> str:
        """Get the creation timestamp."""
        return self._created_at
    
    def get(self) -> bytes:
        """Get the raster data as bytes. Override in subclasses."""
        return b""
    
    def to_json(self) -> str:
        """Convert the analysis to JSON string."""
        import json
        return json.dumps({
            "id": self._id,
            "generator_type": self._generator_type,
            "fire_metadata": self._fire_metadata.to_dict() if self._fire_metadata else None,
            "status": self._status,
            "created_at": self._created_at,
            "raw_raster_url": self._raw_raster_url,
            "source_vector_url": self._source_vector_url,
            "published_dnbr_raster_url": self._published_dnbr_raster_url,
            "published_vector_url": self._published_vector_url
        })
    
    @classmethod
    def from_json(cls, json_str: str) -> 'DNBRAnalysis':
        """Create an analysis from JSON string."""
        import json
        from .fire_metadata import FireMetadata
        
        data = json.loads(json_str)
        
        # Reconstruct fire metadata if it exists
        fire_metadata = None
        if data.get("fire_metadata"):
            fire_metadata = FireMetadata.from_json_data(data["fire_metadata"])
        
        analysis = cls(
            generator_type=data.get("generator_type", "unknown"),
            fire_metadata=fire_metadata
        )
        
        # Override the generated ID with the stored one
        analysis._id = data.get("id", analysis._id)
        analysis._status = data.get("status", "PENDING")
        analysis._created_at = data.get("created_at", analysis._created_at)
        analysis._raw_raster_url = data.get("raw_raster_url")
        analysis._source_vector_url = data.get("source_vector_url")
        analysis._published_dnbr_raster_url = data.get("published_dnbr_raster_url")
        analysis._published_vector_url = data.get("published_vector_url")
        
        return analysis 


    
 