#!/usr/bin/env python3
"""
Leaflet map generation module.
Creates interactive HTML maps from dNBR raster data.
"""

import os
import sys
import geopandas as gpd
from generate_dnbr_utils import create_leaflet_map


def generate_leaflet_map_from_data(aoi_gdf: gpd.GeoDataFrame, raster_path: str, output_path: str = "docs/outputs/fire_severity_map.html") -> str:
    """
    Generate Leaflet map from dNBR raster and AOI data.
    
    Args:
        aoi_gdf: GeoDataFrame containing the area of interest
        raster_path: Path to the dNBR raster file
        output_path: Path for the output HTML file
        
    Returns:
        Path to the generated HTML map file
    """
    print(f"🗺️  Generating Leaflet map from raster: {raster_path}")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Generate the map
    map_path = create_leaflet_map(aoi_gdf, raster_path, output_path)
    
    print(f"✅ Leaflet map generated: {map_path}")
    return map_path


def generate_leaflet_map_standalone(aoi_path: str, raster_path: str = None, output_path: str = "docs/outputs/fire_severity_map.html", analysis_id: str = None) -> str:
    """
    Standalone function to generate Leaflet map from AOI file and raster file.
    This is the main entry point for map generation.
    
    Args:
        aoi_path: Path to AOI GeoJSON file
        raster_path: Path to the dNBR raster file (optional if analysis_id provided)
        output_path: Path for the output HTML file
        analysis_id: Analysis ID to use for raster path (overrides raster_path if provided)
        
    Returns:
        Path to the generated HTML map file
    """
    print(f"🗺️  Generating standalone Leaflet map")
    print(f"📁 AOI: {aoi_path}")
    
    # Determine raster path
    if analysis_id:
        raster_path = f"docs/outputs/{analysis_id}/fire_severity.tif"
        print(f"📊 Raster: {raster_path} (from analysis ID: {analysis_id})")
    else:
        raster_path = raster_path or "docs/outputs/fire_severity.tif"
        print(f"📊 Raster: {raster_path}")
    
    # Load the AOI
    aoi_gdf = gpd.read_file(aoi_path)
    print(f"✅ Loaded AOI with {len(aoi_gdf)} features")
    
    # Generate the map
    map_path = generate_leaflet_map_from_data(aoi_gdf, raster_path, output_path)
    
    print(f"✅ Standalone map generation completed: {map_path}")
    return map_path


def main():
    """Main function for Leaflet map generation."""
    if len(sys.argv) < 2:
        print("Usage: python generate_leaflet.py <aoi_geojson_path> [raster_path] [output_html_path]")
        print("Defaults: raster_path=docs/outputs/fire_severity.tif, output_html_path=docs/outputs/fire_severity_map.html")
        sys.exit(1)
    
    aoi_path = sys.argv[1]
    raster_path = sys.argv[2] if len(sys.argv) > 2 else "docs/outputs/fire_severity.tif"
    output_path = sys.argv[3] if len(sys.argv) > 3 else "docs/outputs/fire_severity_map.html"
    
    # Generate the map using standalone function
    map_path = generate_leaflet_map_standalone(aoi_path, raster_path, output_path)
    print(f"📊 Map output: {map_path}")


if __name__ == "__main__":
    main() 