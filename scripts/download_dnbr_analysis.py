#!/usr/bin/env python3
"""
Download dNBR analysis data.
This script is used by the download_dnbr_analysis.yml GitHub Action.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from dnbr.analysis_service import create_analysis_service
from scripts.generate_leaflet_utils import generate_leaflet_map_standalone


def download_dnbr_data(analysis_id: str, aoi_path: str = "data/fire.geojson"):
    """
    Download dNBR data for a specific analysis and regenerate the map.
    
    Args:
        analysis_id: Analysis ID to download data for
        aoi_path: Path to AOI file
    """
    print(f"📥 Downloading dNBR data for analysis: {analysis_id}")
    
    # Get analysis from database
    service = create_analysis_service()
    analysis = service.get_analysis(analysis_id)
    
    if not analysis:
        print(f"❌ Analysis {analysis_id} not found in database")
        sys.exit(1)
    
    # Check analysis status
    status = analysis.status
    print(f"📊 Analysis status: {status}")
    
    if status == "COMPLETED":
        try:
            # Get the data (this will download if needed)
            data = analysis.get()
            print(f"✅ Data retrieved successfully ({len(data)} bytes)")
            
            # Data is available in the file system
            print("📁 Data available in file system")
            
                                        # Create ULID folder and save the raster data
            import os
            ulid_dir = os.path.join("docs/outputs", analysis.get_id())
            os.makedirs(ulid_dir, exist_ok=True)
            
            raster_path = os.path.join(ulid_dir, "fire_severity.tif")
            with open(raster_path, 'wb') as f:
                f.write(data)
            print(f"✅ Raster data saved to: {raster_path}")
            
            # Generate overlay PNG in the ULID folder
            print("🎨 Generating overlay PNG in ULID folder...")
            from scripts.generate_dnbr_utils import create_raster_overlay_image
            
            overlay_path = os.path.join(ulid_dir, "fire_severity_overlay.png")
            create_raster_overlay_image(raster_path, overlay_path)
            print(f"✅ Overlay PNG generated: {overlay_path}")
            
            print("📁 Data downloaded successfully")
            print(f"💡 To generate map, run the 'Generate Map Shell' workflow with analysis ID: {analysis_id}")
            
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

    parser.add_argument("--aoi-path", default="data/fire.geojson", 
                       help="Path to AOI file")
    args = parser.parse_args()
    
    download_dnbr_data(args.analysis_id, args.aoi_path)


if __name__ == "__main__":
    main() 