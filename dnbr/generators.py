#!/usr/bin/env python3
"""
Abstract base class and factory functions for dNBR generation.
Defines the interface for different dNBR generation methods.
"""

from abc import ABC, abstractmethod
import geopandas as gpd
from .analysis import DNBRAnalysis
from .fire_metadata import FireMetadata, create_fire_metadata_from_feature
from typing import List


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


def create_dnbr_generator(method: str = "dummy", fire_metadata: FireMetadata = None) -> DNBRGenerator:
    """
    Factory function to create appropriate dNBR generator.
    
    Args:
        method: Generation method ("dummy" or "gee")
        fire_metadata: Optional fire metadata object
        
    Returns:
        DNBRGenerator instance
    """
    if method == "dummy":
        from .dummy_generator import DummyDNBRGenerator
        return DummyDNBRGenerator(fire_metadata)
    elif method == "gee":
        from .gee_generator import GEEDNBRGenerator
        return GEEDNBRGenerator(fire_metadata)
    else:
        raise ValueError(f"Unknown dNBR generation method: {method}")


def generate_dnbr(aoi_gdf: gpd.GeoDataFrame, method: str = "dummy", 
                 data_path: str = None, fire_metadata: FireMetadata = None) -> DNBRAnalysis:
    """
    Convenience function to generate dNBR analysis.
    
    Args:
        aoi_gdf: GeoDataFrame containing the area of interest
        method: Generation method ("dummy" or "gee")
        data_path: Path to the data file for metadata extraction
        fire_metadata: Optional fire metadata object
        
    Returns:
        DNBRAnalysis object representing the dNBR generation task
    """
    generator = create_dnbr_generator(method, fire_metadata)
    return generator.generate_dnbr(aoi_gdf, data_path)


def generate_dnbr_batch(layer_gdf: gpd.GeoDataFrame, method: str = "dummy",
                       data_path: str = None, provider: str = "sa_fire") -> List[DNBRAnalysis]:
    """
    Generate dNBR analysis for multiple AOIs in a layer.
    
    Args:
        layer_gdf: GeoDataFrame containing multiple areas of interest
        method: Generation method ("dummy" or "gee")
        data_path: Path to the data file for metadata extraction
        provider: Data provider for metadata extraction ("sa_fire", etc.)
        
    Returns:
        List of DNBRAnalysis objects representing the dNBR generation tasks
    """
    analyses = []
    
    for index, aoi_feature in layer_gdf.iterrows():
        # Create single-feature GeoDataFrame
        single_aoi_gdf = gpd.GeoDataFrame([aoi_feature], crs=layer_gdf.crs)
        
        # Extract metadata from this feature
        fire_metadata = create_fire_metadata_from_feature(aoi_feature, provider)
        
        # Generate analysis for this AOI
        analysis = generate_dnbr(single_aoi_gdf, method=method, 
                               data_path=data_path, fire_metadata=fire_metadata)
        analyses.append(analysis)
    
    return analyses 