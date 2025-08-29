#!/usr/bin/env python3
"""
Publisher for publishing analysis results to various storage systems.
Follows SOLID principles with abstract interfaces and dependency injection.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import boto3
import rasterio
from rasterio.io import MemoryFile
import tempfile
import os
from .analysis import DNBRAnalysis


class AnalysisPublisher(ABC):
    """Abstract base class for publishing analysis results."""
    
    @abstractmethod
    def publish_analysis(self, analysis: DNBRAnalysis, geojson_path: str) -> List[str]:
        """
        Publish analysis results.
        
        Args:
            analysis: Analysis object containing metadata and file paths
            geojson_path: Path to the GeoJSON file to publish
            
        Returns:
            List of published URLs
            
        Raises:
            ValueError: If analysis is missing required data
            FileNotFoundError: If required files don't exist
            RuntimeError: If publishing fails
        """
        pass


class S3AnalysisPublisher(AnalysisPublisher):
    """S3 implementation of analysis publisher."""
    
    def __init__(self, bucket_name: str, region: str = "ap-southeast-2", s3_client=None):
        """
        Initialize S3 publisher.
        
        Args:
            bucket_name: S3 bucket name
            region: AWS region (defaults to ap-southeast-2)
            s3_client: Optional S3 client for dependency injection
        """
        self.bucket_name = bucket_name
        self.region = region
        self.s3_client = s3_client or boto3.client('s3', region_name=region)
    
    def publish_analysis(self, analysis: DNBRAnalysis) -> List[str]:
        """
        Publish analysis to S3.
        
        Args:
            analysis: Analysis object containing source vector URL and raw raster URL
            
        Returns:
            List of S3 URLs for published files
        """
        # Validate inputs
        if analysis.status != "COMPLETED":
            raise ValueError(f"Analysis status must be 'COMPLETED' to publish, got '{analysis.status}'")
        
        if not analysis.get_aoi_id():
            raise ValueError("No aoi_id found in analysis fire metadata")
        
        if not analysis.raw_raster_url:
            raise ValueError("No raw raster URL found in analysis")
        
        if not analysis.source_vector_url:
            raise ValueError("No source vector URL found in analysis")
        
        if not os.path.exists(analysis.raw_raster_url):
            raise FileNotFoundError(f"Raw raster file not found: {analysis.raw_raster_url}")
        
        if not os.path.exists(analysis.source_vector_url):
            raise FileNotFoundError(f"Source vector file not found: {analysis.source_vector_url}")
        
        # Generate COG from raw raster
        cog_path = self._generate_cog_from_file(analysis.raw_raster_url)
        
        try:
            aoi_id = analysis.get_aoi_id()
            analysis_id = analysis.get_id()
            
            # Create S3 key structure: <aoi_id>/<ulid>/dnbr.cog.tif
            s3_prefix = f"{aoi_id}/{analysis_id}"
            
            # Upload COG to S3
            cog_key = f"{s3_prefix}/dnbr.cog.tif"
            self.s3_client.upload_file(cog_path, self.bucket_name, cog_key)
            
            # Upload GeoJSON to S3
            aoi_key = f"{s3_prefix}/aoi.geojson"
            self.s3_client.upload_file(analysis.source_vector_url, self.bucket_name, aoi_key)
            
            # Set published URLs in the analysis object
            analysis._published_dnbr_raster_url = f"s3://{self.bucket_name}/{cog_key}"
            analysis._published_vector_url = f"s3://{self.bucket_name}/{aoi_key}"
            
            # Clean up temporary COG file
            os.unlink(cog_path)
            
            # Return S3 URLs
            s3_urls = [
                analysis._published_dnbr_raster_url,
                analysis._published_vector_url
            ]
            
            return s3_urls
            
        except Exception as e:
            raise RuntimeError(f"Failed to publish analysis to S3: {str(e)}")
    
    def _generate_cog_from_file(self, input_path: str) -> str:
        """
        Generate Cloud Optimized GeoTIFF from input file.
        
        Args:
            input_path: Path to input raster file
            
        Returns:
            Path to generated COG file
        """
        with rasterio.open(input_path) as src:
            # Create temporary file for COG
            with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp_file:
                cog_path = tmp_file.name
            
            # Copy with COG-optimized settings
            with rasterio.open(
                cog_path, 'w',
                driver='GTiff',
                height=src.height,
                width=src.width,
                count=src.count,
                dtype=src.dtypes[0],
                crs=src.crs,
                transform=src.transform,
                tiled=True,
                blockxsize=512,
                blockysize=512,
                compress='lzw',
                overview_level=5,
                overview_resampling='nearest'
            ) as dst:
                dst.write(src.read())
                
                # Build overviews
                dst.build_overviews([2, 4, 8, 16, 32], rasterio.enums.Resampling.nearest)
        
        return cog_path


def create_s3_publisher(bucket_name: str, region: str = "ap-southeast-2", s3_client=None) -> S3AnalysisPublisher:
    """
    Create an S3 publisher for publishing analysis data.
    
    Args:
        bucket_name: S3 bucket name
        region: AWS region (default: ap-southeast-2)
        s3_client: Optional S3 client instance
        
    Returns:
        S3AnalysisPublisher instance
    """
    if not bucket_name:
        raise ValueError("bucket_name is required")
    return S3AnalysisPublisher(bucket_name, region, s3_client) 