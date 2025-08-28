#!/usr/bin/env python3
"""
Abstract base class and factory functions for dNBR generation.
Defines the interface for different dNBR generation methods.
"""

from abc import ABC, abstractmethod
import geopandas as gpd
from .analysis import DNBRAnalysis
from .fire_metadata import FireMetadata


class DNBRGenerator(ABC):
    """Abstract base class for dNBR generation."""
    
    def __init__(self, fire_metadata: FireMetadata = None):
        """
        Initialize generator with optional fire metadata.
        
        Args:
            fire_metadata: Optional fire metadata object
        """
        self.fire_metadata = fire_metadata
    
    @abstractmethod
    def generate_dnbr(self, aoi_gdf: gpd.GeoDataFrame, data_path: str = None) -> DNBRAnalysis:
        """
        Generate dNBR analysis from AOI GeoDataFrame.
        
        Args:
            aoi_gdf: GeoDataFrame containing the area of interest
            data_path: Path to the data file for metadata extraction
            
        Returns:
            DNBRAnalysis object representing the dNBR generation task
        """
        pass


def create_dnbr_generator(method: str = "dummy", output_dir: str = "docs/outputs", 
                         fire_metadata: FireMetadata = None) -> DNBRGenerator:
    """
    Factory function to create appropriate dNBR generator.
    
    Args:
        method: Generation method ("dummy" or "gee")
        output_dir: Directory for output files
        fire_metadata: Optional fire metadata object
        
    Returns:
        DNBRGenerator instance
    """
    if method == "dummy":
        from .dummy_generator import DummyDNBRGenerator
        return DummyDNBRGenerator(output_dir, fire_metadata)
    elif method == "gee":
        from .gee_generator import GEEDNBRGenerator
        return GEEDNBRGenerator(output_dir, fire_metadata)
    else:
        raise ValueError(f"Unknown dNBR generation method: {method}")


def generate_dnbr(aoi_gdf: gpd.GeoDataFrame, method: str = "dummy", output_dir: str = "docs/outputs", 
                 data_path: str = None, fire_metadata: FireMetadata = None) -> DNBRAnalysis:
    """
    Convenience function to generate dNBR analysis.
    
    Args:
        aoi_gdf: GeoDataFrame containing the area of interest
        method: Generation method ("dummy" or "gee")
        output_dir: Directory for output files
        data_path: Path to the data file for metadata extraction
        fire_metadata: Optional fire metadata object
        
    Returns:
        DNBRAnalysis object representing the dNBR generation task
    """
    generator = create_dnbr_generator(method, output_dir, fire_metadata)
    return generator.generate_dnbr(aoi_gdf, data_path) 