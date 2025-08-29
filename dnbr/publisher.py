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
import json
from datetime import datetime
from .analysis import DNBRAnalysis


class AnalysisPublisher(ABC):
    """Abstract base class for publishing analysis results."""
    
    @abstractmethod
    def publish_analysis(self, analysis: DNBRAnalysis) -> List[str]:
        """
        Publish analysis results.
        
        Args:
            analysis: Analysis object containing metadata and file paths
            
        Returns:
            List of published URLs
            
        Raises:
            ValueError: If analysis is missing required data
            FileNotFoundError: If required files don't exist
            RuntimeError: If publishing fails
        """
        pass


class S3AnalysisPublisher(AnalysisPublisher):
    """S3 implementation of analysis publisher with STAC structure."""
    
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
        Publish analysis to S3 with STAC structure.
        
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
            job_id = analysis.get_job_id() or analysis.get_id()  # Use job_id if available, fallback to analysis_id
            fire_metadata = analysis.fire_metadata
            
            # Generate filenames using metadata
            raster_filename = fire_metadata.generate_filename("raster")
            vector_filename = fire_metadata.generate_filename("vector")
            
            # Create STAC structure:
            # s3://bucket/jobs/{job_id}/{aoi_id}/dnbr.cog.tif
            # s3://bucket/jobs/{job_id}/{aoi_id}/aoi.geojson
            # s3://bucket/stac/collections/fires.json
            # s3://bucket/stac/items/{job_id}/{aoi_id}.json
            
            # Upload raw data to jobs directory
            job_prefix = f"jobs/{job_id}/{aoi_id}"
            raster_key = f"{job_prefix}/{raster_filename}"
            vector_key = f"{job_prefix}/{vector_filename}"
            
            self.s3_client.upload_file(cog_path, self.bucket_name, raster_key)
            self.s3_client.upload_file(analysis.source_vector_url, self.bucket_name, vector_key)
            
            # Create STAC item
            stac_item = self._create_stac_item(analysis, raster_key, vector_key)
            stac_item_key = f"stac/items/{job_id}/{aoi_id}.json"
            
            # Upload STAC item
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=stac_item_key,
                Body=json.dumps(stac_item, indent=2),
                ContentType='application/json'
            )
            
            # Update STAC collection to point to this job
            self._update_stac_collection(job_id)
            
            # Set published URLs in the analysis object
            analysis._published_dnbr_raster_url = f"s3://{self.bucket_name}/{raster_key}"
            analysis._published_vector_url = f"s3://{self.bucket_name}/{vector_key}"
            
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
    
    def _create_stac_item(self, analysis: DNBRAnalysis, raster_key: str, vector_key: str) -> dict:
        """
        Create STAC item for the analysis.
        
        Args:
            analysis: Analysis object
            raster_key: S3 key for raster file
            vector_key: S3 key for vector file
            
        Returns:
            STAC item dictionary
        """
        aoi_id = analysis.get_aoi_id()
        job_id = analysis.get_job_id() or analysis.get_id()  # Use job_id if available, fallback to analysis_id
        fire_metadata = analysis.fire_metadata
        
        # Read geometry from source vector file
        import geopandas as gpd
        gdf = gpd.read_file(analysis.source_vector_url)
        geometry = gdf.iloc[0].geometry.__geo_interface__
        
        stac_item = {
            "id": f"{aoi_id}_{job_id}",
            "type": "Feature",
            "collection": "fires",
            "geometry": geometry,
            "properties": {
                "aoi_id": aoi_id,
                "job_id": job_id,
                "fire_date": fire_metadata.get_date(),
                "provider": fire_metadata.get_provider(),
                "analysis_method": analysis.generator_type,
                "datetime": analysis.get_created_at(),
                "status": analysis.status
            },
            "assets": {
                "dnbr": {
                    "href": f"s3://{self.bucket_name}/{raster_key}",
                    "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                    "title": "dNBR Analysis Result"
                },
                "aoi": {
                    "href": f"s3://{self.bucket_name}/{vector_key}",
                    "type": "application/geo+json",
                    "title": "Area of Interest Boundary"
                }
            },
            "links": [
                {
                    "rel": "collection",
                    "href": "/stac/collections/fires"
                },
                {
                    "rel": "self",
                    "href": f"/stac/items/{job_id}/{aoi_id}"
                }
            ]
        }
        
        return stac_item
    
    def _update_stac_collection(self, job_id: str):
        """
        Update STAC collection to point to the current job.
        
        Args:
            job_id: Job ID to set as current
        """
        collection = {
            "id": "fires",
            "title": "Fire Severity Analysis",
            "description": "dNBR analysis results for fire AOIs",
            "type": "Collection",
            "stac_version": "1.0.0",
            "extent": {
                "spatial": {
                    "bbox": [138.0, -35.0, 141.0, -32.0]  # South Australia
                },
                "temporal": {
                    "interval": [["2019-01-01", "2024-12-31"]]
                }
            },
            "links": [
                {
                    "rel": "items",
                    "href": f"/stac/collections/fires/items/{job_id}"
                },
                {
                    "rel": "self",
                    "href": "/stac/collections/fires"
                }
            ]
        }
        
        # Upload STAC collection
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key="stac/collections/fires.json",
            Body=json.dumps(collection, indent=2),
            ContentType='application/json'
        )
    
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