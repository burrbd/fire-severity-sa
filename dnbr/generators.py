#!/usr/bin/env python3
"""
Abstract base class and factory functions for dNBR generation.
Defines the interface for different dNBR generation methods.
"""

from abc import ABC, abstractmethod
import geopandas as gpd
from .analysis import DNBRAnalysis


class DNBRGenerator(ABC):
    """Abstract base class for dNBR generation."""
    
    @abstractmethod
    def generate_dnbr(self, aoi_gdf: gpd.GeoDataFrame) -> DNBRAnalysis:
        """
        Generate dNBR analysis from AOI GeoDataFrame.
        
        Args:
            aoi_gdf: GeoDataFrame containing the area of interest
            
        Returns:
            DNBRAnalysis object representing the dNBR generation task
        """
        pass


def create_dnbr_generator(method: str = "dummy", output_dir: str = "docs/outputs") -> DNBRGenerator:
    """
    Factory function to create appropriate dNBR generator.
    
    Args:
        method: Generation method ("dummy" or "gee")
        output_dir: Directory for output files
        
    Returns:
        DNBRGenerator instance
    """
    if method == "dummy":
        from .dummy_generator import DummyDNBRGenerator
        return DummyDNBRGenerator(output_dir)
    elif method == "gee":
        from .gee_generator import GEEDNBRGenerator
        return GEEDNBRGenerator(output_dir)
    else:
        raise ValueError(f"Unknown dNBR generation method: {method}")


def generate_dnbr(aoi_gdf: gpd.GeoDataFrame, method: str = "dummy", output_dir: str = "docs/outputs") -> DNBRAnalysis:
    """
    Convenience function to generate dNBR analysis.
    
    Args:
        aoi_gdf: GeoDataFrame containing the area of interest
        method: Generation method ("dummy" or "gee")
        output_dir: Directory for output files
        
    Returns:
        DNBRAnalysis object representing the dNBR generation task
    """
    generator = create_dnbr_generator(method, output_dir)
    return generator.generate_dnbr(aoi_gdf) 