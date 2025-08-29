#!/usr/bin/env python3
"""
Dummy dNBR generator for testing and development.
"""

import os
import geopandas as gpd
from .generators import DNBRGenerator
from .analysis import DNBRAnalysis
from .fire_metadata import FireMetadata, create_fire_metadata


class DummyDNBRGenerator(DNBRGenerator):
    """Dummy dNBR generator for testing and development."""
    
    def __init__(self, output_dir: str = "docs/outputs", fire_metadata: FireMetadata = None):
        super().__init__(fire_metadata)
        self.output_dir = output_dir
    
    def generate_dnbr(self, aoi_gdf: gpd.GeoDataFrame, data_path: str = None) -> DNBRAnalysis:
        """
        Generate dummy dNBR analysis for testing.
        
        Args:
            aoi_gdf: GeoDataFrame containing the area of interest
            data_path: Path to the data file for metadata extraction
            
        Returns:
            DNBRAnalysis object with metadata pointing to existing dummy data
        """
        # Create fire metadata if data path is provided and no metadata exists
        fire_metadata = self.fire_metadata
        if not fire_metadata and data_path:
            try:
                fire_metadata = create_fire_metadata("sa_fire", geojson_path=data_path)
            except Exception as e:
                print(f"Warning: Could not create fire metadata: {e}")
        
        # Create a simple DNBRAnalysis object with fire metadata
        analysis = DNBRAnalysis(
            generator_type="dummy",
            fire_metadata=fire_metadata
        )
        
        # Set the path to the existing dummy raster file
        # The publisher will handle reading this file and converting to COG
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        
        # Set the source vector URL to the input data path
        if data_path:
            analysis._source_vector_url = data_path
        
        # Set status to COMPLETED since dummy data is always available synchronously
        analysis.set_status("COMPLETED")
        
        return analysis 