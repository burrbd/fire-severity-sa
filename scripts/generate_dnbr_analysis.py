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
from dnbr.generators import generate_dnbr_batch
from dnbr.analysis_service import create_analysis_service
from dnbr.publisher import create_s3_publisher


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
    print(f"📁 AOI Layer: {aoi_path}")
    print(f"🔧 Method: {method}")
    print(f"📊 Provider: {provider}")
    
    # Load the AOI layer
    try:
        layer_gdf = load_aoi(aoi_path)
        print(f"✅ Loaded AOI layer with {len(layer_gdf)} features")
    except Exception as e:
        print(f"❌ Failed to load AOI layer: {e}")
        sys.exit(1)
    
    # Step 1: Generate dNBR analyses for all AOIs in the layer
    print(f"📊 Generating dNBR analyses for {len(layer_gdf)} AOIs using {method} method...")
    try:
        analyses = generate_dnbr_batch(layer_gdf, method=method, data_path=aoi_path, provider=provider)
        print(f"✅ Generated {len(analyses)} dNBR analyses")
        
        # Display summary of generated analyses
        for i, analysis in enumerate(analyses, 1):
            print(f"   {i}. Analysis ID: {analysis.get_id()}")
            if analysis.get_aoi_id():
                print(f"      AOI ID: {analysis.get_aoi_id()}")
            if analysis.get_fire_date():
                print(f"      Fire Date: {analysis.get_fire_date()}")
            print(f"      Status: {analysis.status}")
            
    except Exception as e:
        print(f"❌ Failed to generate dNBR analyses: {e}")
        sys.exit(1)
    
    # Step 2: Store all analyses in DynamoDB
    print(f"💾 Storing {len(analyses)} analyses in DynamoDB...")
    try:
        service = create_analysis_service()
        stored_count = 0
        
        for analysis in analyses:
            service.store_analysis(analysis)
            stored_count += 1
            print(f"   ✅ Stored analysis {stored_count}/{len(analyses)}: {analysis.get_id()}")
        
        print(f"✅ All {stored_count} analyses stored in DynamoDB")
    except Exception as e:
        print(f"❌ Failed to store analyses in DynamoDB: {e}")
        sys.exit(1)
    
    # Step 3: Publish analyses to S3 (if S3 bucket is configured)
    s3_bucket = os.environ.get('AWS_S3_BUCKET_NAME')
    if s3_bucket:
        print(f"☁️ Publishing {len(analyses)} analyses to S3 bucket: {s3_bucket}")
        try:
            publisher = create_s3_publisher(
                bucket_name=s3_bucket,
                region=os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')
            )
            
            published_count = 0
            for analysis in analyses:
                try:
                    s3_urls = publisher.publish_analysis(analysis)
                    published_count += 1
                    print(f"   ✅ Published analysis {published_count}/{len(analyses)}: {analysis.get_id()}")
                    for url in s3_urls:
                        print(f"      📁 {url}")
                except Exception as e:
                    print(f"   ⚠️ Failed to publish analysis {analysis.get_id()}: {e}")
            
            print(f"✅ Published {published_count}/{len(analyses)} analyses to S3")
        except Exception as e:
            print(f"⚠️ Failed to publish to S3: {e}")
            print("   Continuing without S3 publishing...")
    else:
        print("ℹ️ S3 publishing skipped (AWS_S3_BUCKET_NAME not set)")
    
    # Output analysis IDs for GitHub Actions
    analysis_ids = [analysis.get_id() for analysis in analyses]
    print(f"🔗 Analysis IDs: {', '.join(analysis_ids)}")
    
    print("🎉 dNBR analysis generation completed successfully!")
    print(f"📊 Generated {len(analyses)} analyses for {len(layer_gdf)} AOIs")
    print("💡 To publish data to S3, run the publish-dnbr-analysis action")


if __name__ == "__main__":
    main() 