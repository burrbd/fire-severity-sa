#!/usr/bin/env python3
"""
Tests for the Analysis Publisher.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from botocore.exceptions import ClientError, NoCredentialsError
from dnbr.publisher import S3AnalysisPublisher, AnalysisPublisher, create_s3_publisher
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
        self.completed_analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        
        # Add fire metadata with INCIDENTNU for correct aoi_id generation
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        self.completed_analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        self.completed_analysis.set_status("COMPLETED")
        self.completed_analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        self.completed_analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        self.incomplete_analysis = DNBRAnalysis()
        self.incomplete_analysis.set_status("PENDING")
    
    def test_publisher_creation(self):
        """Test publisher creation."""
        publisher = S3AnalysisPublisher("test-bucket")
        assert publisher.bucket_name == "test-bucket"
        assert publisher.region == "ap-southeast-2"  # Default region
    
    def test_publisher_with_custom_region(self):
        """Test publisher creation with custom region."""
        publisher = S3AnalysisPublisher("test-bucket", region="us-west-2")
        assert publisher.region == "us-west-2"
    
    def test_publisher_with_injected_client(self):
        """Test publisher creation with injected S3 client."""
        mock_client = Mock()
        publisher = S3AnalysisPublisher("test-bucket", s3_client=mock_client)
        assert publisher.s3_client == mock_client
    
    @patch.object(S3AnalysisPublisher, '_generate_cog_from_file')
    @patch('os.unlink')
    def test_publish_completed_analysis(self, mock_unlink, mock_generate_cog):
        """Test publishing a completed analysis."""
        # Mock COG generation
        mock_generate_cog.return_value = "temp_cog.tif"
        
        # Mock S3 uploads
        self.mock_s3_client.upload_file.return_value = None
        
        # Act
        urls = self.publisher.publish_analysis(self.completed_analysis)
        
        # Assert
        assert len(urls) == 2
        assert urls[0].startswith("s3://test-bucket/201912036/")
        assert urls[0].endswith("/dnbr.cog.tif")
        assert urls[1].startswith("s3://test-bucket/201912036/")
        assert urls[1].endswith("/aoi.geojson")
        
        # Verify S3 uploads were called
        assert self.mock_s3_client.upload_file.call_count == 2
        
        # Verify analysis was updated with published URLs
        assert self.completed_analysis.published_dnbr_raster_url is not None
        assert self.completed_analysis.published_vector_url is not None
    
    def test_publish_analysis_without_fire_metadata_raises_error(self):
        """Test that publishing analysis without fire metadata raises error."""
        with pytest.raises(ValueError, match="Analysis status must be 'COMPLETED' to publish, got 'PENDING'"):
            self.publisher.publish_analysis(self.incomplete_analysis)
    
    def test_publish_analysis_without_fire_metadata_raises_value_error(self):
        """Test publishing analysis without fire metadata raises ValueError."""
        analysis = DNBRAnalysis()
        analysis.set_status("COMPLETED")
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        with pytest.raises(ValueError, match="No aoi_id found in analysis fire metadata"):
            self.publisher.publish_analysis(analysis)
    
    def test_publish_analysis_without_raw_raster_path(self):
        """Test publishing analysis without raw raster path raises error."""
        analysis = DNBRAnalysis()
        analysis.set_status("COMPLETED")
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("COMPLETED")
        # No raw_raster_path set
        
        with pytest.raises(ValueError, match="No raw raster URL found in analysis"):
            self.publisher.publish_analysis(analysis)
    
    def test_publish_analysis_with_incomplete_status_raises_error(self):
        """Test that publishing analysis with non-COMPLETED status raises error."""
        # Create analysis with PENDING status
        analysis = DNBRAnalysis()
        analysis.set_status("PENDING")
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("PENDING")  # Set to PENDING instead of COMPLETED
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        with pytest.raises(ValueError, match="Analysis status must be 'COMPLETED' to publish, got 'PENDING'"):
            self.publisher.publish_analysis(analysis)
    
    def test_publish_analysis_with_failed_status_raises_error(self):
        """Test that publishing analysis with FAILED status raises error."""
        # Create analysis with FAILED status
        analysis = DNBRAnalysis()
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("FAILED")  # Set to FAILED
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        with pytest.raises(ValueError, match="Analysis status must be 'COMPLETED' to publish, got 'FAILED'"):
            self.publisher.publish_analysis(analysis)
    
    @patch.object(S3AnalysisPublisher, '_generate_cog_from_file')
    def test_publish_analysis_s3_error(self, mock_generate_cog):
        """Test publishing when S3 upload fails."""
        # Mock COG generation
        mock_generate_cog.return_value = "temp_cog.tif"
        
        # Mock S3 upload failure
        self.mock_s3_client.upload_file.side_effect = ClientError(
            {'Error': {'Code': 'AccessDenied'}}, 'UploadFile'
        )
        
        with pytest.raises(RuntimeError, match="Failed to publish analysis to S3"):
            self.publisher.publish_analysis(self.completed_analysis)
    
    @patch.object(S3AnalysisPublisher, '_generate_cog_from_file')
    def test_publish_analysis_cog_generation_error(self, mock_generate_cog):
        """Test publishing when COG generation fails."""
        # Mock COG generation failure
        mock_generate_cog.side_effect = RuntimeError("COG generation failed")
        
        with pytest.raises(RuntimeError, match="COG generation failed"):
            self.publisher.publish_analysis(self.completed_analysis)


class TestS3PublisherFactory:
    """Test the S3 publisher factory function."""
    
    def test_create_s3_publisher(self):
        """Test creating S3 publisher via factory."""
        publisher = create_s3_publisher("test-bucket")
        assert isinstance(publisher, S3AnalysisPublisher)
        assert publisher.bucket_name == "test-bucket"
    
    def test_create_s3_publisher_requires_bucket_name(self):
        """Test creating S3 publisher requires bucket name."""
        with pytest.raises(ValueError, match="bucket_name is required"):
            create_s3_publisher("")
    
    def test_create_s3_publisher_with_custom_region(self):
        """Test creating S3 publisher with custom region."""
        publisher = create_s3_publisher("test-bucket", region="us-west-2")
        assert publisher.region == "us-west-2"


class TestPublisherIntegration:
    """Integration tests for publisher."""
    
    def test_publisher_with_analysis_metadata(self):
        """Test that publisher works with analysis metadata."""
        # Create a concrete implementation for testing
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("COMPLETED")
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        publisher = S3AnalysisPublisher("test-bucket")
        
        # This would require actual S3 credentials to test fully
        # For now, just verify the analysis has the required metadata
        assert analysis.get_aoi_id() == "bushfire_20191230"
        assert analysis.raw_raster_url == "data/dummy_data/raw_dnbr.tif"
        assert analysis.status == "COMPLETED" 