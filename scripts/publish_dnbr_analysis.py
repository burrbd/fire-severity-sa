#!/usr/bin/env python3
"""
Publish dNBR analysis data to S3.
This script is used by the publish_dnbr_analysis.yml GitHub Action.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from dnbr.analysis_service import create_analysis_service
from dnbr.publisher import create_s3_publisher


def publish_dnbr_data(analysis_id: str, aoi_path: str = "data/dummy_data/fire.geojson"):
    """
    Publish dNBR data for a specific analysis to S3.
    
    Args:
        analysis_id: Analysis ID to publish data for
        aoi_path: Path to AOI file
    """
    print(f"☁️ Publishing dNBR data for analysis: {analysis_id}")
    
    # Get analysis from database
    service = create_analysis_service()
    analysis = service.get_analysis(analysis_id)
    
    if not analysis:
        print(f"❌ Analysis {analysis_id} not found in database")
        sys.exit(1)
    
    # Check analysis status
    status = analysis.status
    print(f"📊 Analysis status: {status}")
    
    if status != "COMPLETED":
        print(f"❌ Analysis not complete (status: {status})")
        print(f"   Only analyses with status 'COMPLETED' can be published to S3")
        print(f"   Current status: '{status}'")
        sys.exit(1)
    
    # Check if analysis has required data
    if not analysis.raw_raster_path:
        print(f"❌ Analysis missing raw raster path")
        sys.exit(1)
    
    if not analysis.get_fire_id():
        print(f"❌ Analysis missing fire metadata")
        sys.exit(1)
    
    # Get S3 bucket from environment
    s3_bucket = os.environ.get('AWS_S3_BUCKET_NAME')
    if not s3_bucket:
        print(f"❌ AWS_S3_BUCKET_NAME environment variable not set")
        sys.exit(1)
    
    try:
        # Create S3 publisher
        publisher = create_s3_publisher(
            bucket_name=s3_bucket,
            region=os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')
        )
        
        # Publish analysis to S3
        print(f"📤 Publishing to S3 bucket: {s3_bucket}")
        s3_urls = publisher.publish_analysis(analysis, aoi_path)
        
        print(f"✅ Analysis published successfully to S3:")
        for url in s3_urls:
            print(f"   📁 {url}")
        
        # Update analysis with published URLs
        service.store_analysis(analysis)
        print(f"✅ Analysis updated with S3 URLs in database")
        
        print(f"🎉 Publishing completed successfully!")
        print(f"💡 Analysis ID: {analysis_id}")
        print(f"🔥 Fire ID: {analysis.get_fire_id()}")
        
    except Exception as e:
        print(f"❌ Failed to publish to S3: {e}")
        sys.exit(1)


def main():
    """Main function for publishing dNBR data."""
    parser = argparse.ArgumentParser(description="Publish dNBR analysis data to S3")
    parser.add_argument("--analysis-id", required=True, help="Analysis ID to publish")
    parser.add_argument("--aoi-path", default="data/dummy_data/fire.geojson", 
                       help="Path to AOI file")
    args = parser.parse_args()
    
    publish_dnbr_data(args.analysis_id, args.aoi_path)


if __name__ == "__main__":
    main()
