#!/usr/bin/env python3
"""
Main dNBR analysis job script using the new polymorphic job architecture.
This script creates and executes jobs using the specified method.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geopandas as gpd
from scripts.generate_dnbr_utils import load_aoi
from dnbr.jobs import create_job
from dnbr.job_service import create_job_service


def main():
    """Main pipeline function for dNBR analysis job execution."""
    if len(sys.argv) < 2:
        print("Usage: python dnbr_analysis_job.py <aoi_geojson_path> [method] [provider]")
        print("Methods: dummy (default), gee")
        print("Providers: sa_fire (default), etc.")
        sys.exit(1)
    
    aoi_path = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "dummy"
    provider = sys.argv[3] if len(sys.argv) > 3 else "sa_fire"
    
    print(f"🔥 Fire Severity Analysis - dNBR Analysis Job")
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
    
    # Step 1: Create and execute job
    print(f"📊 Creating and executing {method} job for {len(layer_gdf)} AOIs...")
    try:
        # Create job using factory
        job = create_job(method, layer_gdf, provider=provider)
        
        # Execute job
        result_job = job.execute()
        
        print(f"✅ Job executed successfully")
        print(f"   🆔 Job ID: {result_job.get_id()}")
        print(f"   📊 Analysis Count: {result_job.get_analysis_count()}")
        print(f"   ✅ Completed: {len(result_job.get_completed_analyses())}")
        print(f"   ⏳ Pending: {len(result_job.get_pending_analyses())}")
        print(f"   ❌ Failed: {len(result_job.get_failed_analyses())}")
        
        # Display summary of generated analyses
        for i, analysis in enumerate(result_job.get_analyses(), 1):
            print(f"   {i}. AOI ID: {analysis.get_aoi_id()}")
            print(f"      Status: {analysis.status}")
            if analysis.get_fire_date():
                print(f"      Fire Date: {analysis.get_fire_date()}")
            
    except Exception as e:
        print(f"❌ Failed to execute job: {e}")
        sys.exit(1)
    
    # Step 2: Store job in DynamoDB
    print(f"💾 Storing job in DynamoDB...")
    try:
        job_service = create_job_service()
        job_service.store_job(result_job)
        
        print(f"✅ Job stored in DynamoDB: {result_job.get_id()}")
        print(f"   📊 Contains {result_job.get_analysis_count()} analyses")
    except Exception as e:
        print(f"❌ Failed to store job in DynamoDB: {e}")
        sys.exit(1)
    
    # Note: Publishing is handled separately by the publish-dnbr-analysis action
    print("ℹ️ Publishing will be handled by the publish-dnbr-analysis action")
    
    # Output job ID for GitHub Actions
    print(f"🔗 Job ID: {result_job.get_id()}")
    
    print("🎉 dNBR analysis job completed successfully!")
    print(f"📊 Created {result_job.get_analysis_count()} analyses for {len(layer_gdf)} AOIs")
    print(f"💡 To publish completed analyses to S3, run the publish-dnbr-analysis action")


if __name__ == "__main__":
    main()
