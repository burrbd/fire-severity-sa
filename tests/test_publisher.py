#!/usr/bin/env python3
"""
Tests for the Analysis Publisher.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from botocore.exceptions import ClientError, NoCredentialsError
from dnbr.publisher import S3AnalysisPublisher, AnalysisPublisher, create_publisher
from dnbr.analysis import DNBRAnalysis
from dnbr.fire_metadata import SAFireMetadata


class TestS3AnalysisPublisher:
    """Test the S3 Analysis Publisher."""
    
    def setup_method(self):
        """Set up test data."""
        # Create mock S3 client
        self.mock_s3_client = Mock()
        
        # Create publisher with injected mock client
        self.publisher = S3AnalysisPublisher("test-bucket", s3_client=self.mock_s3_client)
        
        # Create test analyses
        self.completed_analysis = DNBRAnalysis()
        self.completed_analysis.set_status("COMPLETED")
        self.completed_analysis._raw_raster_path = "data/dummy_data/raw_dnbr.tif"
        
        # Add fire metadata
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        self.completed_analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        self.completed_analysis.set_status("COMPLETED")
        self.completed_analysis._raw_raster_path = "data/dummy_data/raw_dnbr.tif"
        
        self.incomplete_analysis = DNBRAnalysis()
        self.incomplete_analysis.set_status("PENDING")
    
    def test_publisher_creation(self):
        """Test publisher creation."""
        publisher = S3AnalysisPublisher("test-bucket")
        assert publisher.bucket_name == "test-bucket"
        assert publisher.region == "us-east-1"
    
    def test_publisher_with_custom_region(self):
        """Test publisher creation with custom region."""
        publisher = S3AnalysisPublisher("test-bucket", region="us-west-2")
        assert publisher.region == "us-west-2"
    
    def test_publisher_with_injected_client(self):
        """Test publisher creation with injected S3 client."""
        mock_client = Mock()
        publisher = S3AnalysisPublisher("test-bucket", s3_client=mock_client)
        assert publisher.s3_client == mock_client
    
    @patch('dnbr.publisher.generate_cog_from_file')
    def test_publish_completed_analysis(self, mock_generate_cog):
        """Test publishing a completed analysis."""
        # Mock COG generation
        mock_generate_cog.return_value = "temp_cog.tif"
        
        # Mock S3 uploads
        self.mock_s3_client.upload_file.return_value = None
        
        # Act
        urls = self.publisher.publish_analysis(self.completed_analysis, "data/dummy_data/fire.geojson")
        
        # Assert
        assert len(urls) == 2
        assert urls[0].startswith("s3://test-bucket/bushfire_20191230/")
        assert urls[0].endswith("/dnbr.cog.tif")
        assert urls[1].startswith("s3://test-bucket/bushfire_20191230/")
        assert urls[1].endswith("/aoi.geojson")
        
        # Verify S3 uploads were called
        assert self.mock_s3_client.upload_file.call_count == 2
        
        # Verify analysis was updated with published URLs
        assert self.completed_analysis.published_dnbr_raster_url is not None
        assert self.completed_analysis.published_vector_url is not None
    
    def test_publish_incomplete_analysis_raises_error(self):
        """Test that publishing incomplete analysis raises error."""
        with pytest.raises(ValueError, match="Cannot publish incomplete analysis"):
            self.publisher.publish_analysis(self.incomplete_analysis, "data/dummy_data/fire.geojson")
    
    def test_publish_analysis_without_fire_metadata(self):
        """Test publishing analysis without fire metadata raises error."""
        analysis = DNBRAnalysis()
        analysis.set_status("COMPLETED")
        analysis._raw_raster_path = "data/dummy_data/raw_dnbr.tif"
        
        with pytest.raises(RuntimeError, match="No fire_id found in analysis fire metadata"):
            self.publisher.publish_analysis(analysis, "data/dummy_data/fire.geojson")
    
    def test_publish_analysis_without_raw_raster_path(self):
        """Test publishing analysis without raw raster path raises error."""
        analysis = DNBRAnalysis()
        analysis.set_status("COMPLETED")
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("COMPLETED")
        # No raw_raster_path set
        
        with pytest.raises(RuntimeError, match="No raw raster file path found in analysis"):
            self.publisher.publish_analysis(analysis, "data/dummy_data/fire.geojson")
    
    @patch('dnbr.publisher.generate_cog_from_file')
    def test_publish_analysis_s3_error(self, mock_generate_cog):
        """Test publishing when S3 upload fails."""
        # Mock COG generation
        mock_generate_cog.return_value = "temp_cog.tif"
        
        # Mock S3 upload failure
        self.mock_s3_client.upload_file.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'UploadFile'
        )
        
        with pytest.raises(RuntimeError, match="S3 upload failed"):
            self.publisher.publish_analysis(self.completed_analysis, "data/dummy_data/fire.geojson")
    
    @patch('dnbr.publisher.generate_cog_from_file')
    def test_publish_analysis_cog_generation_error(self, mock_generate_cog):
        """Test publishing when COG generation fails."""
        # Mock COG generation failure
        mock_generate_cog.side_effect = RuntimeError("COG generation failed")
        
        with pytest.raises(RuntimeError, match="Publishing failed"):
            self.publisher.publish_analysis(self.completed_analysis, "data/dummy_data/fire.geojson")


class TestPublisherFactory:
    """Test the publisher factory function."""
    
    def test_create_s3_publisher(self):
        """Test creating S3 publisher via factory."""
        publisher = create_publisher("s3", bucket_name="test-bucket")
        assert isinstance(publisher, S3AnalysisPublisher)
        assert publisher.bucket_name == "test-bucket"
    
    def test_create_s3_publisher_default_bucket(self):
        """Test creating S3 publisher with default bucket."""
        publisher = create_publisher("s3")
        assert isinstance(publisher, S3AnalysisPublisher)
        assert publisher.bucket_name == "fire-severity-analyses"
    
    def test_create_unknown_publisher(self):
        """Test creating unknown publisher type raises error."""
        with pytest.raises(ValueError, match="Unknown publisher type"):
            create_publisher("unknown")


class TestPublisherIntegration:
    """Integration tests for publisher."""
    
    def test_publisher_with_analysis_metadata(self):
        """Test that publisher works with analysis metadata."""
        # Create a concrete implementation for testing
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("COMPLETED")
        analysis._raw_raster_path = "data/dummy_data/raw_dnbr.tif"
        
        publisher = S3AnalysisPublisher("test-bucket")
        
        # This would require actual S3 credentials to test fully
        # For now, just verify the analysis has the required metadata
        assert analysis.get_fire_id() == "bushfire_20191230"
        assert analysis.raw_raster_path == "data/dummy_data/raw_dnbr.tif"
        assert analysis.status == "COMPLETED" 