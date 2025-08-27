#!/usr/bin/env python3
"""
GEE-based dNBR generator for real processing.
"""

import geopandas as gpd
from .generators import DNBRGenerator
from .analysis import DNBRAnalysis


class GEEDNBRGenerator(DNBRGenerator):
    """GEE-based dNBR generator for real processing."""
    
    def __init__(self, output_dir: str = "docs/outputs"):
        self.output_dir = output_dir
    
    def generate_dnbr(self, aoi_gdf: gpd.GeoDataFrame) -> DNBRAnalysis:
        """
        Generate dNBR analysis using Google Earth Engine.
        
        Args:
            aoi_gdf: GeoDataFrame containing the area of interest
            
        Returns:
            DNBRAnalysis object representing the submitted analysis
        """
        # Create a simple DNBRAnalysis object
        analysis = DNBRAnalysis(generator_type="gee")
        
        return analysis 