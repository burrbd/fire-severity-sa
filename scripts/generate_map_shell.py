#!/usr/bin/env python3
"""
Generate Leaflet map shell from AOI and raster data.
This script is used by the generate_map_shell.yml GitHub Action.
"""

import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geopandas as gpd
from scripts.generate_leaflet_utils import generate_leaflet_map_standalone


def main():
    """Main function to generate Leaflet map from AOI file."""
    parser = argparse.ArgumentParser(description="Generate Leaflet map shell from AOI and raster data")
    parser.add_argument("aoi_path", help="Path to AOI GeoJSON file")
    parser.add_argument("--analysis-id", help="Analysis ID (ULID) to use for raster data")
    
    args = parser.parse_args()
    
    print(f"🗺️  Generating Leaflet map")
    print(f"📁 AOI: {args.aoi_path}")
    
    try:
        if args.analysis_id:
            print(f"📊 Using analysis ID: {args.analysis_id}")
            # Generate map with specific analysis ID
            map_path = generate_leaflet_map_standalone(args.aoi_path, analysis_id=args.analysis_id)
        else:
            print(f"📊 Using default raster data")
            # Generate map with default raster path
            map_path = generate_leaflet_map_standalone(args.aoi_path)
        
        print(f"✅ Map generated successfully: {map_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate map: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 