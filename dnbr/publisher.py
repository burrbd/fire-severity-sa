#!/usr/bin/env python3
"""
Analysis Publisher for uploading analysis data to S3.
This module handles the final step of making analysis data available for maps.
"""

from abc import ABC, abstractmethod
from typing import List
from .analysis import DNBRAnalysis


class AnalysisPublisher(ABC):
    """Abstract base class for publishing analysis data to storage."""
    
    @abstractmethod
    def publish_analysis(self, analysis: DNBRAnalysis) -> List[str]:
        """
        Publish analysis data to storage and return URLs.
        
        Args:
            analysis: Completed analysis object to publish
            
        Returns:
            List of URLs where the data is now available
            
        Raises:
            ValueError: If analysis is not completed
            RuntimeError: If publishing fails
        """
        pass


class S3AnalysisPublisher(AnalysisPublisher):
    """S3 implementation of analysis publisher."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """
        Initialize S3 publisher.
        
        Args:
            bucket_name: S3 bucket name for storing analysis data
            region: AWS region for the bucket
        """
        self.bucket_name = bucket_name
        self.region = region
        # TODO: Initialize boto3 S3 client when AWS credentials are available
    
    def publish_analysis(self, analysis: DNBRAnalysis) -> List[str]:
        """
        Publish analysis data to S3.
        
        Args:
            analysis: Completed analysis object to publish
            
        Returns:
            List of S3 URLs where the data is now available
        """
        # Validate analysis is completed
        if analysis.status != "COMPLETED":
            raise ValueError(f"Cannot publish incomplete analysis (status: {analysis.status})")
        
        # TODO: Implement publishing functionality
        # 1. Get raster data from analysis
        # 2. Extract bounds and generate overlay PNG
        # 3. Upload both files to S3
        # 4. Return S3 URLs
        
        # For now, return dummy S3 URLs
        s3_urls = [
            f"s3://{self.bucket_name}/analyses/{analysis.get_id()}/fire_severity.tif",
            f"s3://{self.bucket_name}/analyses/{analysis.get_id()}/fire_severity_overlay.png"
        ]
        
        return s3_urls
    
    def _process_raster_data(self, raster_data: bytes) -> tuple:
        """
        Process raster data to extract bounds and generate overlay PNG.
        
        Args:
            raster_data: Raw raster data as bytes
            
        Returns:
            Tuple of (bounds, overlay_data) where bounds is [south, west, north, east]
            and overlay_data is PNG bytes
        """
        import tempfile
        import os
        import rasterio
        import numpy as np
        import matplotlib.pyplot as plt
        from .generators import create_dnbr_colormap
        
        # Create temporary file to read with rasterio
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as temp_file:
            temp_file.write(raster_data)
            temp_path = temp_file.name
        
        try:
            # Read the raster data and extract bounds
            with rasterio.open(temp_path) as src:
                data = src.read(1)  # Read first band
                bounds = src.bounds
                
                # Convert bounds to [south, west, north, east] format
                bounds_list = [bounds.bottom, bounds.left, bounds.top, bounds.right]
            
            # Generate overlay PNG
            # Normalize data to 0-1 range for visualization
            data_normalized = (data - data.min()) / (data.max() - data.min())
            
            # Get the colormap
            cmap = create_dnbr_colormap()
            
            # Apply colormap to normalized data
            colored_data = cmap(data_normalized)
            
            # Create PNG in memory
            plt.figure(figsize=(10, 10))
            plt.imshow(colored_data)
            plt.axis('off')
            
            # Save to bytes buffer
            import io
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', pad_inches=0, 
                       transparent=True, dpi=150)
            plt.close()
            
            overlay_data = buffer.getvalue()
            
            return bounds_list, overlay_data
            
        finally:
            # Clean up temporary file
            os.unlink(temp_path)
    



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
        return S3AnalysisPublisher(bucket_name, region)
    else:
        raise ValueError(f"Unknown publisher type: {publisher_type}") 