#!/usr/bin/env python3
"""
Download dNBR data and regenerate map.
This script is used by the download-dnbr-job.yml GitHub Action.
"""

import sys
import os
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dnbr.generators import create_analysis_from_id
from generate_leaflet_utils import generate_leaflet_map_standalone


def download_dnbr_data(analysis_id: str, generator_type: str, aoi_path: str = "data/fire.geojson"):
    """
    Download dNBR data for a specific analysis and regenerate the map.
    
    Args:
        analysis_id: Analysis ID to download data for
        generator_type: Generator type ("dummy" or "gee")
        aoi_path: Path to AOI file
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
            
            # Regenerate map with the analysis's data
            print("🗺️  Regenerating map...")
            # For dummy analysis, use the actual raster path from the analysis
            if generator_type == "dummy":
                map_path = generate_leaflet_map_standalone(aoi_path, raster_path=analysis._result_path)
            else:
                map_path = generate_leaflet_map_standalone(aoi_path, analysis_id=analysis_id)
            print(f"✅ Map regenerated: {map_path}")
            
        except Exception as e:
            print(f"❌ Failed to get data: {e}")
            sys.exit(1)
    else:
        print(f"❌ Analysis not complete (status: {status})")
        sys.exit(1)


def main():
    """Main function for downloading dNBR data."""
    parser = argparse.ArgumentParser(description="Download dNBR data and regenerate map")
    parser.add_argument("--analysis-id", required=True, help="Analysis ID to download")
    parser.add_argument("--generator-type", required=True, choices=["dummy", "gee"], 
                       help="Generator type")
    parser.add_argument("--aoi-path", default="data/fire.geojson", 
                       help="Path to AOI file")
    
    args = parser.parse_args()
    
    download_dnbr_data(args.analysis_id, args.generator_type, args.aoi_path)


if __name__ == "__main__":
    main() 