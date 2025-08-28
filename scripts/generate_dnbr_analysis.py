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
from dnbr.analysis_service import create_analysis_service
from dnbr.publisher import create_s3_publisher
from dnbr.fire_metadata import create_fire_metadata


def main():
    """Main pipeline function for dNBR analysis generation."""
    if len(sys.argv) < 2:
        print("Usage: python generate_dnbr_analysis.py <aoi_geojson_path> [method] [provider]")
        print("Methods: dummy (default), gee")
        print("Providers: sa_fire (default), etc.")
        print("Note: Use 'python generate_map_shell.py <aoi_path>' to generate maps separately")
        sys.exit(1)
    
    aoi_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "dummy"
    provider = sys.argv[3] if len(sys.argv) > 3 else "sa_fire"
    
    print(f"🔥 Fire Severity Analysis - dNBR Analysis Generation")
    print(f"📁 AOI: {aoi_path}")
    print(f"🔧 Method: {method}")
    print(f"📊 Provider: {provider}")
    
    # Load the AOI
    try:
        aoi_gdf = load_aoi(aoi_path)
        print(f"✅ Loaded AOI with {len(aoi_gdf)} features")
    except Exception as e:
        print(f"❌ Failed to load AOI: {e}")
        sys.exit(1)
    
    # Create fire metadata
    fire_metadata = None
    try:
        fire_metadata = create_fire_metadata(provider, geojson_path=aoi_path)
        print(f"✅ Created fire metadata for provider: {provider}")
        print(f"🔥 Fire ID: {fire_metadata.get_id()}")
        print(f"📅 Fire Date: {fire_metadata.get_date()}")
    except Exception as e:
        print(f"⚠️ Could not create fire metadata: {e}")
        print("   Continuing without fire metadata...")
    
    # Step 1: Generate dNBR analysis using dummy generator
    print(f"📊 Generating dNBR analysis using {method} method...")
    try:
        analysis = generate_dnbr(aoi_gdf, method=method, data_path=aoi_path, fire_metadata=fire_metadata)
        print(f"✅ dNBR analysis created: {analysis.get_id()}")
        print(f"📊 Analysis status: {analysis.status}")
        if analysis.get_aoi_id():
            print(f"🔥 AOI ID: {analysis.get_aoi_id()}")
        if analysis.get_fire_date():
            print(f"📅 Fire Date: {analysis.get_fire_date()}")
        if analysis.get_provider():
            print(f"🏢 Provider: {analysis.get_provider()}")
    except Exception as e:
        print(f"❌ Failed to generate dNBR analysis: {e}")
        sys.exit(1)
    
    # Step 2: Store analysis in DynamoDB
    print(f"💾 Storing analysis in DynamoDB...")
    try:
        service = create_analysis_service()
        service.store_analysis(analysis)
        print(f"✅ Analysis stored in DynamoDB: {analysis.get_id()}")
    except Exception as e:
        print(f"❌ Failed to store analysis in DynamoDB: {e}")
        sys.exit(1)
    
    # Step 3: Publish analysis to S3 (if S3 bucket is configured)
    s3_bucket = os.environ.get('AWS_S3_BUCKET_NAME')
    if s3_bucket:
        print(f"☁️ Publishing analysis to S3 bucket: {s3_bucket}")
        try:
            publisher = create_s3_publisher(
                bucket_name=s3_bucket,
                region=os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')
            )
            s3_urls = publisher.publish_analysis(analysis, aoi_path)
            print(f"✅ Analysis published to S3:")
            for url in s3_urls:
                print(f"   📁 {url}")
        except Exception as e:
            print(f"⚠️ Failed to publish to S3: {e}")
            print("   Continuing without S3 publishing...")
    else:
        print("ℹ️ S3 publishing skipped (AWS_S3_BUCKET_NAME not set)")
    
    # Output analysis ID for GitHub Actions
    print(f"🔗 Analysis ID: {analysis.get_id()}")
    
    print("🎉 dNBR analysis generation completed successfully!")
    print("💡 To publish data to S3, run the publish-dnbr-analysis action")


if __name__ == "__main__":
    main() 