#!/usr/bin/env python3
"""
Publish dNBR analysis data to S3.
This script is used by the publish_dnbr_analysis.yml GitHub Action.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from dnbr.publisher import create_s3_publisher


def publish_dnbr_data(job_id: str):
    """
    Publish dNBR data for a specific job to S3.
    
    Args:
        job_id: Job ID to publish data for
    """
    print(f"☁️ Publishing dNBR data for job: {job_id}")
    
    # Get job from database
    from dnbr.job_service import create_job_service
    service = create_job_service()
    job = service.get_job(job_id)
    
    if not job:
        print(f"❌ Job {job_id} not found in database")
        sys.exit(1)
    
    # Get all analyses from the job
    analyses = job.get_analyses()
    print(f"📊 Job contains {len(analyses)} analyses")
    
    # Check if all analyses are completed
    completed_analyses = [a for a in analyses if a.status == "COMPLETED"]
    if len(completed_analyses) != len(analyses):
        print(f"❌ Not all analyses are complete")
        print(f"   Completed: {len(completed_analyses)}/{len(analyses)}")
        print(f"   Only jobs with all analyses 'COMPLETED' can be published to S3")
        sys.exit(1)
    
    # Check if all analyses have required data
    for analysis in analyses:
        if not analysis.raw_raster_url:
            print(f"❌ Analysis {analysis.get_aoi_id()} missing raw raster URL")
            sys.exit(1)
        
        if not analysis.source_vector_url:
            print(f"❌ Analysis {analysis.get_aoi_id()} missing source vector URL")
            sys.exit(1)
        
        if not analysis.get_aoi_id():
            print(f"❌ Analysis missing aoi metadata")
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
        
        # Publish all analyses in the job to S3
        print(f"📤 Publishing {len(analyses)} analyses to S3 bucket: {s3_bucket}")
        published_count = 0
        
        for analysis in analyses:
            try:
                s3_urls = publisher.publish_analysis(analysis)
                published_count += 1
                print(f"   ✅ Published analysis {published_count}/{len(analyses)}: {analysis.get_aoi_id()}")
                for url in s3_urls:
                    print(f"      📁 {url}")
            except Exception as e:
                print(f"   ⚠️ Failed to publish analysis {analysis.get_aoi_id()}: {e}")
        
        # Update job with published URLs
        service.store_job(job)
        print(f"✅ Job updated with S3 URLs in database")
        
        print(f"🎉 Publishing completed successfully!")
        print(f"💡 Job ID: {job_id}")
        print(f"📊 Published: {published_count}/{len(analyses)} analyses")
        
    except Exception as e:
        print(f"❌ Failed to publish to S3: {e}")
        sys.exit(1)


def main():
    """Main function for publishing dNBR job data."""
    parser = argparse.ArgumentParser(description="Publish dNBR job data to S3")
    parser.add_argument("--job-id", required=True, help="Job ID to publish")
    args = parser.parse_args()
    
    publish_dnbr_data(args.job_id)


if __name__ == "__main__":
    main()
