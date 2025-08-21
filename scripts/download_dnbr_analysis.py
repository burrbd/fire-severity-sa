#!/usr/bin/env python3
"""
Download dNBR analysis data.
This script is used by the download_dnbr_analysis.yml GitHub Action.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from dnbr.generators import create_analysis_from_id
from scripts.generate_leaflet_utils import generate_leaflet_map_standalone


def download_dnbr_data(analysis_id: str, generator_type: str, aoi_path: str = "data/fire.geojson", data_only: bool = False):
    """
    Download dNBR data for a specific analysis and optionally regenerate the map.
    
    Args:
        analysis_id: Analysis ID to download data for
        generator_type: Generator type ("dummy" or "gee")
        aoi_path: Path to AOI file
        data_only: If True, only download data without regenerating map
    """
    print(f"📥 Downloading dNBR data for analysis: {analysis_id}")
    print(f"🔧 Generator type: {generator_type}")
    
    # Create analysis object from ID and type
    analysis = create_analysis_from_id(analysis_id, generator_type)
    
    # Check analysis status
    status = analysis.status()
    print(f"📊 Analysis status: {status}")
    
    if status == "COMPLETED":
        try:
            # Get the data (this will download if needed)
            data = analysis.get()
            print(f"✅ Data retrieved successfully ({len(data)} bytes)")
            
            # For dummy analyses, data is already in the file system
            # For GEE analyses, this would download the data
            if generator_type == "dummy":
                print("📁 Dummy data already available in file system")
            else:
                print("☁️  GEE data downloaded from cloud storage")
            
            if not data_only:
                # Regenerate map with the analysis's data
                print("🗺️  Regenerating map...")
                # Use the ULID-based raster path from the analysis
                map_path = generate_leaflet_map_standalone(aoi_path, raster_path=analysis._result_path)
                print(f"✅ Map regenerated: {map_path}")
            else:
                print("📁 Data downloaded successfully (map generation skipped)")
                print(f"💡 To generate map, run: python scripts/generate_map.py {aoi_path} --analysis-id {analysis_id}")
            
        except Exception as e:
            print(f"❌ Failed to get data: {e}")
            sys.exit(1)
    else:
        print(f"❌ Analysis not complete (status: {status})")
        sys.exit(1)


def main():
    """Main function for downloading dNBR data."""
    parser = argparse.ArgumentParser(description="Download dNBR analysis data")
    parser.add_argument("--analysis-id", required=True, help="Analysis ID to download")
    parser.add_argument("--generator-type", required=True, choices=["dummy", "gee"], 
                       help="Generator type")
    parser.add_argument("--aoi-path", default="data/fire.geojson", 
                       help="Path to AOI file")
    parser.add_argument("--data-only", action="store_true",
                       help="Only download data without regenerating map")
    
    args = parser.parse_args()
    
    download_dnbr_data(args.analysis_id, args.generator_type, args.aoi_path, args.data_only)


if __name__ == "__main__":
    main() 