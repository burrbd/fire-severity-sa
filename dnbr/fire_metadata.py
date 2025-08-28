#!/usr/bin/env python3
"""
Fire metadata abstraction for different fire data providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import re
from datetime import datetime


class FireMetadata(ABC):
    """Abstract base class for fire metadata."""
    
    @abstractmethod
    def get_id(self) -> str:
        """
        Get the unique area of interest identifier.
        
        Returns:
            String identifier for the area of interest
        """
        pass
    
    @abstractmethod
    def get_date(self) -> str:
        """
        Get the fire date.
        
        Returns:
            String representation of the fire date
        """
        pass
    
    @abstractmethod
    def get_provider(self) -> str:
        """
        Get the data provider name.
        
        Returns:
            String name of the data provider
        """
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert metadata to dictionary for serialization.
        
        Returns:
            Dictionary representation of the metadata
        """
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FireMetadata':
        """
        Create metadata from dictionary.
        
        Args:
            data: Dictionary containing metadata
            
        Returns:
            FireMetadata instance
        """
        pass
    
    @classmethod
    def from_json_data(cls, data: Dict[str, Any]) -> 'FireMetadata':
        """
        Create appropriate FireMetadata from JSON data.
        This is a factory method that determines the correct type based on provider.
        
        Args:
            data: Dictionary containing metadata with provider field
            
        Returns:
            FireMetadata instance of the appropriate type
        """
        provider = data.get("provider")
        if provider == "sa_fire":
            return SAFireMetadata.from_dict(data)
        else:
            raise ValueError(f"Unknown fire metadata provider: {provider}")


class SAFireMetadata(FireMetadata):
    """Fire metadata for South Australia Fire data."""
    
    def __init__(self, incident_type: str, fire_date: str, raw_properties: Dict[str, Any]):
        """
        Initialize SA Fire metadata.
        
        Args:
            incident_type: Type of incident (e.g., "Bushfire")
            fire_date: Date of the fire (e.g., "30/12/2019")
            raw_properties: Raw properties from GeoJSON
        """
        self.incident_type = incident_type
        self.fire_date = fire_date
        self.raw_properties = raw_properties
        self._aoi_id = self._generate_aoi_id()
    
    def _generate_aoi_id(self) -> str:
        """Generate a sanitized area of interest ID from incident number and date."""
        try:
            date_obj = datetime.strptime(self.fire_date, '%d/%m/%Y')
            date_str = date_obj.strftime('%Y%m%d')
        except ValueError:
            # If date parsing fails, use the original string but sanitize it
            date_str = re.sub(r'[^0-9]', '', self.fire_date)
        
        # Use INCIDENTNU if available, otherwise fall back to incident type
        incident_number = self.raw_properties.get('INCIDENTNU')
        if incident_number:
            # Use the incident number directly as it should be unique
            return str(incident_number)
        else:
            # Fall back to sanitized incident type for use in file paths
            incident_safe = re.sub(r'[^a-zA-Z0-9]', '_', self.incident_type.lower())
            return f"{incident_safe}_{date_str}"
    
    def get_id(self) -> str:
        """Get the unique area of interest identifier."""
        return self._aoi_id
    
    def get_date(self) -> str:
        """Get the fire date."""
        return self.fire_date
    
    def get_provider(self) -> str:
        """Get the data provider name."""
        return "sa_fire"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary for serialization."""
        return {
            "aoi_id": self._aoi_id,
            "fire_date": self.fire_date,
            "provider": self.get_provider(),
            "provider_metadata": {
                "incident_type": self.incident_type,
                "raw_properties": self.raw_properties
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SAFireMetadata':
        """Create metadata from dictionary."""
        provider_metadata = data.get("provider_metadata", {})
        incident_type = provider_metadata.get("incident_type", "Unknown")
        fire_date = data.get("fire_date", "Unknown")
        raw_properties = provider_metadata.get("raw_properties", {})
        
        return cls(incident_type, fire_date, raw_properties)
    
    @classmethod
    def from_geojson(cls, geojson_path: str) -> 'SAFireMetadata':
        """
        Create SA Fire metadata from GeoJSON file.
        
        Args:
            geojson_path: Path to the GeoJSON file
            
        Returns:
            SAFireMetadata instance
            
        Raises:
            ValueError: If required properties are missing
            FileNotFoundError: If GeoJSON file doesn't exist
        """
        try:
            with open(geojson_path, 'r') as f:
                data = json.load(f)
            
            if not data.get('features'):
                raise ValueError("No features found in GeoJSON")
            
            properties = data['features'][0]['properties']
            incident_type = properties.get('INCIDENTTY', 'Unknown')
            fire_date = properties.get('FIREDATE', 'Unknown')
            
            if not fire_date or fire_date == 'Unknown':
                raise ValueError("FIREDATE property is required")
            
            return cls(incident_type, fire_date, properties)
            
        except FileNotFoundError:
            raise FileNotFoundError(f"GeoJSON file not found: {geojson_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in file: {geojson_path}")


def create_fire_metadata(provider: str = "sa_fire", **kwargs) -> FireMetadata:
    """
    Factory function to create appropriate fire metadata.
    
    Args:
        provider: Data provider ("sa_fire", etc.)
        **kwargs: Additional arguments (e.g., geojson_path for sa_fire)
        
    Returns:
        FireMetadata instance
    """
    if provider == "sa_fire":
        geojson_path = kwargs.get("geojson_path")
        if geojson_path:
            return SAFireMetadata.from_geojson(geojson_path)
        else:
            raise ValueError("geojson_path is required for sa_fire provider")
    else:
        raise ValueError(f"Unknown fire metadata provider: {provider}")
