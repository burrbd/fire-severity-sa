#!/usr/bin/env python3
"""
Generate Leaflet map from AOI and raster data.
This script is used by the generate-gh-pages.yml GitHub Action.
"""

import sys
import geopandas as gpd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generate_leaflet_utils import generate_leaflet_map_standalone


def main():
    """Main function to generate Leaflet map from AOI file."""
    if len(sys.argv) != 2:
        print("Usage: python generate_map.py <aoi_geojson_path>")
        sys.exit(1)
    
    aoi_path = sys.argv[1]
    
    print(f"🗺️  Generating Leaflet map")
    print(f"📁 AOI: {aoi_path}")
    
    try:
        # Generate map (uses default raster path)
        map_path = generate_leaflet_map_standalone(aoi_path)
        print(f"✅ Map generated successfully: {map_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate map: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 