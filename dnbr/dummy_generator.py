#!/usr/bin/env python3
"""
Dummy dNBR generator for testing and development.
"""

import os
import shutil
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
        
        # Create ULID-based output directory
        analysis_dir = os.path.join(self.output_dir, analysis.get_id())
        os.makedirs(analysis_dir, exist_ok=True)
        
        # Copy pre-committed dummy raster to ULID folder
        source_path = "data/dummy/fire_severity.tif"
        target_path = os.path.join(analysis_dir, "fire_severity.tif")
        
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Pre-committed dummy raster not found: {source_path}")
        
        shutil.copy2(source_path, target_path)
        
        # Update analysis to use the ULID-based path
        analysis._result_path = target_path
        
        print(f"📁 Copied dummy raster to ULID folder: {target_path}")
        
        return analysis 