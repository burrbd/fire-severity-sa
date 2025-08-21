#!/usr/bin/env python3
"""
Main dNBR analysis generation script for GitHub Actions.
This script generates dNBR analyses using the specified method.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geopandas as gpd
from scripts.generate_dnbr_utils import load_aoi
from dnbr.generators import generate_dnbr


def main():
    """Main pipeline function for dNBR analysis generation."""
    if len(sys.argv) < 2:
        print("Usage: python generate_dnbr_analysis.py <aoi_geojson_path> [method]")
        print("Methods: dummy (default), gee")
        print("Note: Use 'python generate_map_shell.py <aoi_path>' to generate maps separately")
        sys.exit(1)
    
    aoi_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "dummy"
    
    print(f"🔥 Fire Severity Analysis - dNBR Analysis Generation")
    print(f"📁 AOI: {aoi_path}")
    print(f"🔧 Method: {method}")
    
    # Load the AOI
    try:
        aoi_gdf = load_aoi(aoi_path)
        print(f"✅ Loaded AOI with {len(aoi_gdf)} features")
    except Exception as e:
        print(f"❌ Failed to load AOI: {e}")
        sys.exit(1)
    
    # Generate dNBR analysis
    print(f"📊 Generating dNBR analysis using {method} method...")
    try:
        analysis = generate_dnbr(aoi_gdf, method=method)
        print(f"✅ dNBR analysis created: {analysis.get_id()}")
        print(f"📊 Analysis status: {analysis.status()}")
        
        # Output analysis ID for GitHub Actions
        print(f"🔗 Analysis ID: {analysis.get_id()}")
        
    except Exception as e:
        print(f"❌ Failed to generate dNBR analysis: {e}")
        sys.exit(1)
    
    print("🎉 dNBR analysis generation completed successfully!")
    print("💡 To download data and generate map, run the download-dnbr-job action")


if __name__ == "__main__":
    main() 