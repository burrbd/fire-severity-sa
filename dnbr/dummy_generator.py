#!/usr/bin/env python3
"""
Dummy dNBR generator for testing and development.
"""

import os
import geopandas as gpd
from .generators import DNBRGenerator
from .dummy_analysis import DummyAnalysis


class DummyDNBRGenerator(DNBRGenerator):
    """Dummy dNBR generator for testing and development."""
    
    def __init__(self, output_dir: str = "docs/outputs"):
        self.output_dir = output_dir
    
    def generate_dnbr(self, aoi_gdf: gpd.GeoDataFrame) -> DummyAnalysis:
        """
        Generate dummy dNBR analysis for testing.
        
        Args:
            aoi_gdf: GeoDataFrame containing the area of interest
            
        Returns:
            DummyAnalysis object containing the generated data
        """
        # Create analysis (this generates the ULID)
        analysis = DummyAnalysis()
        
        # For dummy analysis, we use pre-committed raster data
        # No need to generate or copy files - just return the analysis
        print(f"📁 Using pre-committed dummy raster: {analysis._result_path}")
        
        return analysis 