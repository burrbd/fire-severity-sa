#!/usr/bin/env python3
"""
Polymorphic job classes for dNBR analysis execution.
Each job type implements its own execution logic.
"""

from abc import ABC, abstractmethod
import geopandas as gpd
from typing import List
from .job import DNBRAnalysisJob
from .analysis import DNBRAnalysis
from .fire_metadata import create_fire_metadata_from_feature


class Job(ABC):
    """Abstract base class for dNBR analysis jobs."""
    
    def __init__(self, aoi_layer: gpd.GeoDataFrame, provider: str = "sa_fire"):
        """
        Initialize a job with AOI layer.
        
        Args:
            aoi_layer: GeoDataFrame containing areas of interest
            provider: Data provider for metadata extraction
        """
        self.aoi_layer = aoi_layer
        self.provider = provider
    
    @abstractmethod
    def execute(self) -> DNBRAnalysisJob:
        """
        Execute the job and return a populated DNBRAnalysisJob.
        
        Returns:
            DNBRAnalysisJob with analyses for all AOIs
        """
        pass


class DummyJob(Job):
    """Dummy job for testing and development."""
    
    def execute(self) -> DNBRAnalysisJob:
        """
        Execute dummy job synchronously.
        
        Returns:
            DNBRAnalysisJob with completed analyses
        """
        # Create job
        job = DNBRAnalysisJob(generator_type="dummy")
        
        # Process each AOI
        for index, aoi_feature in self.aoi_layer.iterrows():
            # Create single-feature GeoDataFrame
            single_aoi_gdf = gpd.GeoDataFrame([aoi_feature], crs=self.aoi_layer.crs)
            
            # Extract metadata from this feature
            fire_metadata = create_fire_metadata_from_feature(aoi_feature, self.provider)
            
            # Create analysis
            analysis = DNBRAnalysis(
                generator_type="dummy",
                fire_metadata=fire_metadata,
                job_id=job.get_id()
            )
            
            # Set dummy data paths
            analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
            analysis._source_vector_url = "data/dummy_data/fires.geojson"
            
            # Set status to COMPLETED (synchronous)
            analysis.set_status("COMPLETED")
            
            # Add to job
            job.add_analysis(analysis)
        
        return job


class GEEJob(Job):
    """Google Earth Engine job for real fire severity analysis."""
    
    def execute(self) -> DNBRAnalysisJob:
        """
        Execute GEE job asynchronously.
        
        Returns:
            DNBRAnalysisJob with pending analyses
        """
        # Create job
        job = DNBRAnalysisJob(generator_type="gee")
        
        # Process each AOI
        for index, aoi_feature in self.aoi_layer.iterrows():
            # Create single-feature GeoDataFrame
            single_aoi_gdf = gpd.GeoDataFrame([aoi_feature], crs=self.aoi_layer.crs)
            
            # Extract metadata from this feature
            fire_metadata = create_fire_metadata_from_feature(aoi_feature, self.provider)
            
            # Create analysis
            analysis = DNBRAnalysis(
                generator_type="gee",
                fire_metadata=fire_metadata,
                job_id=job.get_id()
            )
            
            # Set status to PENDING (asynchronous)
            analysis.set_status("PENDING")
            
            # Add to job
            job.add_analysis(analysis)
        
        return job


def create_job(job_type: str, aoi_layer: gpd.GeoDataFrame, provider: str = "sa_fire") -> Job:
    """
    Factory function to create appropriate job type.
    
    Args:
        job_type: Type of job ("dummy" or "gee")
        aoi_layer: GeoDataFrame containing areas of interest
        provider: Data provider for metadata extraction
        
    Returns:
        Job instance
        
    Raises:
        ValueError: If job_type is unknown
    """
    if job_type == "dummy":
        return DummyJob(aoi_layer, provider)
    elif job_type == "gee":
        return GEEJob(aoi_layer, provider)
    else:
        raise ValueError(f"Unknown job type: {job_type}")
