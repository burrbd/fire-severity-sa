#!/usr/bin/env python3
"""
Analysis Publisher for uploading analysis data to S3.
This module handles the final step of making analysis data available for maps.
"""

from abc import ABC, abstractmethod
from typing import List
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from .analysis import DNBRAnalysis


def generate_cog_from_file(input_path: str, output_path: str) -> str:
    """
    Generate a Cloud Optimized GeoTIFF (COG) from an existing raster file.
    
    Args:
        input_path: Path to the input raster file
        output_path: Path where the COG file should be saved
        
    Returns:
        Path to the generated COG file
        
    Raises:
        RuntimeError: If COG generation fails
        FileNotFoundError: If input file doesn't exist
    """
    import os
    import rasterio
    from rasterio.warp import reproject, Resampling
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input raster file not found: {input_path}")
    
    try:
        # Read the source raster
        with rasterio.open(input_path) as src:
            # Create COG with proper compression and tiling
            profile = src.profile.copy()
            profile.update({
                'driver': 'GTiff',
                'compress': 'lzw',
                'tiled': True,
                'blockxsize': 512,
                'blockysize': 512,
                'photometric': 'minisblack',
                'interleave': 'pixel'
            })
            
            # Write COG
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(src.read())
                
                # Add overviews for better web serving
                dst.build_overviews([2, 4, 8, 16], Resampling.nearest)
                dst.update_tags(ns='rio_overview', resampling='nearest')
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to generate COG: {str(e)}")


class AnalysisPublisher(ABC):
    """Abstract base class for publishing analysis data to storage."""
    
    @abstractmethod
    def publish_analysis(self, analysis: DNBRAnalysis, geojson_path: str) -> List[str]:
        """
        Publish analysis data to storage and return URLs.
        
        Args:
            analysis: Completed analysis object to publish
            geojson_path: Path to the GeoJSON file for uploading to S3
            
        Returns:
            List of URLs where the data is now available
            
        Raises:
            ValueError: If analysis is not completed
            RuntimeError: If publishing fails
        """
        pass


class S3AnalysisPublisher(AnalysisPublisher):
    """S3 implementation of analysis publisher."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1", s3_client=None):
        """
        Initialize S3 publisher.
        
        Args:
            bucket_name: S3 bucket name for storing analysis data
            region: AWS region for the bucket
            s3_client: Optional S3 client for dependency injection
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = s3_client or boto3.client('s3', region_name=region)
    
    def publish_analysis(self, analysis: DNBRAnalysis, geojson_path: str) -> List[str]:
        """
        Publish analysis data to S3.
        
        Args:
            analysis: Completed analysis object to publish
            geojson_path: Path to the GeoJSON file for uploading to S3
            
        Returns:
            List of S3 URLs where the data is now available
        """
        # Validate analysis is completed
        if analysis.status != "COMPLETED":
            raise ValueError(f"Cannot publish incomplete analysis (status: {analysis.status})")
        
        try:
            # Use fire metadata from the analysis
            fire_id = analysis.get_fire_id()
            fire_date = analysis.get_fire_date()
            
            if not fire_id:
                raise RuntimeError("No fire_id found in analysis fire metadata")
            
            analysis_id = analysis.get_id()
            
            # Create S3 key structure: <fire_id>/<ulid>/dnbr.cog.tif
            s3_prefix = f"{fire_id}/{analysis_id}"
            
            # Get the raw raster file path from the analysis
            raw_raster_path = analysis.raw_raster_path
            if not raw_raster_path:
                raise RuntimeError("No raw raster file path found in analysis")
            
            # Create temporary COG file
            import tempfile
            import os
            with tempfile.NamedTemporaryFile(suffix='.cog.tif', delete=False) as temp_cog:
                cog_path = temp_cog.name
            
            try:
                # Generate COG from the raw raster file
                generate_cog_from_file(raw_raster_path, cog_path)
                
                # Upload COG to S3
                cog_key = f"{s3_prefix}/dnbr.cog.tif"
                self.s3_client.upload_file(
                    cog_path, 
                    self.bucket_name, 
                    cog_key,
                    ExtraArgs={'ContentType': 'image/tiff'}
                )
                
                # Upload GeoJSON to S3
                aoi_key = f"{s3_prefix}/aoi.geojson"
                self.s3_client.upload_file(
                    geojson_path,
                    self.bucket_name,
                    aoi_key,
                    ExtraArgs={'ContentType': 'application/geo+json'}
                )
                
                # Set published URLs in the analysis object
                analysis._published_dnbr_raster_url = f"s3://{self.bucket_name}/{cog_key}"
                analysis._published_vector_url = f"s3://{self.bucket_name}/{aoi_key}"
                
                # Return S3 URLs
                s3_urls = [
                    analysis._published_dnbr_raster_url,
                    analysis._published_vector_url
                ]
                
                return s3_urls
                
            finally:
                # Clean up temporary COG file
                if os.path.exists(cog_path):
                    os.unlink(cog_path)
                    
        except (ClientError, NoCredentialsError) as e:
            raise RuntimeError(f"S3 upload failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Publishing failed: {str(e)}")


def create_publisher(publisher_type: str = "s3", **kwargs) -> AnalysisPublisher:
    """
    Factory function to create appropriate publisher.
    
    Args:
        publisher_type: Publisher type ("s3")
        **kwargs: Additional arguments for publisher initialization
        
    Returns:
        AnalysisPublisher instance
    """
    if publisher_type == "s3":
        bucket_name = kwargs.get("bucket_name", "fire-severity-analyses")
        region = kwargs.get("region", "us-east-1")
        s3_client = kwargs.get("s3_client")
        return S3AnalysisPublisher(bucket_name, region, s3_client)
    else:
        raise ValueError(f"Unknown publisher type: {publisher_type}") 