#!/usr/bin/env python3
"""
Dummy dNBR generator for testing and development.
"""

import os
import shutil
import geopandas as gpd
from .generators import DNBRGenerator
from .analysis import DNBRAnalysis


class DummyDNBRGenerator(DNBRGenerator):
    """Dummy dNBR generator for testing and development."""
    
    def __init__(self, output_dir: str = "docs/outputs"):
        self.output_dir = output_dir
    
    def generate_dnbr(self, aoi_gdf: gpd.GeoDataFrame) -> DNBRAnalysis:
        """
        Generate dummy dNBR analysis for testing.
        
        Args:
            aoi_gdf: GeoDataFrame containing the area of interest
            
        Returns:
            DNBRAnalysis object with dummy metadata
        """
        # Create a simple DNBRAnalysis object
        analysis = DNBRAnalysis(generator_type="dummy")
        

        
        
        return analysis 