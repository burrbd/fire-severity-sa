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
import json


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
        assert urls[0].startswith("s3://test-bucket/jobs/")
        assert urls[0].endswith("/201912036_dnbr.cog.tif")
        assert urls[1].startswith("s3://test-bucket/jobs/")
        assert urls[1].endswith("/201912036_aoi.geojson")
        
        # Verify S3 uploads were called (2 file uploads + 1 STAC item + 1 STAC collection)
        assert self.mock_s3_client.upload_file.call_count == 2
        assert self.mock_s3_client.put_object.call_count == 2
        
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
    """Integration tests for publisher with analysis metadata."""
    
    def test_publisher_with_analysis_metadata(self):
        """Test publisher integration with analysis metadata."""
        # Create analysis with fire metadata
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        analysis.set_status("COMPLETED")
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.upload_file.return_value = None
        mock_s3_client.put_object.return_value = None
        
        # Create publisher
        publisher = S3AnalysisPublisher("test-bucket", s3_client=mock_s3_client)
        
        # Mock COG generation and file operations
        with patch.object(S3AnalysisPublisher, '_generate_cog_from_file') as mock_cog, \
             patch('os.unlink') as mock_unlink:
            mock_cog.return_value = "temp_cog.tif"
            
            # Publish analysis
            urls = publisher.publish_analysis(analysis)
            
            # Verify behavior: should return S3 URLs
            assert len(urls) == 2
            assert all(url.startswith("s3://test-bucket/") for url in urls)
    
    def test_publisher_uses_job_id_for_s3_structure(self):
        """Test that publisher uses job_id for S3 structure when available."""
        # Create analysis with job_id
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata, job_id="JOB123")
        analysis.set_status("COMPLETED")
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.upload_file.return_value = None
        mock_s3_client.put_object.return_value = None
        
        # Create publisher
        publisher = S3AnalysisPublisher("test-bucket", s3_client=mock_s3_client)
        
        # Mock COG generation and file operations
        with patch.object(S3AnalysisPublisher, '_generate_cog_from_file') as mock_cog, \
             patch('os.unlink') as mock_unlink:
            mock_cog.return_value = "temp_cog.tif"
            
            # Publish analysis
            urls = publisher.publish_analysis(analysis)
            
            # Verify behavior: S3 keys should use job_id, not analysis_id
            assert len(urls) == 2
            
            # Check that S3 uploads used job_id in the key
            upload_calls = mock_s3_client.upload_file.call_args_list
            assert len(upload_calls) == 2
            
            # Verify S3 keys contain job_id
            for call in upload_calls:
                s3_key = call[0][2]  # Third argument is the key for upload_file
                assert "JOB123" in s3_key, f"S3 key should contain job_id: {s3_key}"
                assert "jobs/JOB123/" in s3_key, f"S3 key should use job structure: {s3_key}"
    
    def test_publisher_creates_stac_structure_with_job_id(self):
        """Test that publisher creates STAC structure organized by job_id."""
        # Create analysis with job_id
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata, job_id="JOB123")
        analysis.set_status("COMPLETED")
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.upload_file.return_value = None
        mock_s3_client.put_object.return_value = None
        
        # Create publisher
        publisher = S3AnalysisPublisher("test-bucket", s3_client=mock_s3_client)
        
        # Mock COG generation and file operations
        with patch.object(S3AnalysisPublisher, '_generate_cog_from_file') as mock_cog, \
             patch('os.unlink') as mock_unlink:
            mock_cog.return_value = "temp_cog.tif"
            
            # Publish analysis
            publisher.publish_analysis(analysis)
            
            # Verify behavior: STAC items should be organized by job_id
            put_object_calls = mock_s3_client.put_object.call_args_list
            assert len(put_object_calls) == 2  # STAC item + STAC collection
            
            # Check STAC item key uses job_id
            stac_item_call = put_object_calls[0]
            stac_item_key = stac_item_call[1]['Key']  # Key parameter
            assert "stac/items/JOB123/" in stac_item_key, f"STAC item should use job_id: {stac_item_key}"
            
            # Check STAC collection points to job_id
            stac_collection_call = put_object_calls[1]
            stac_collection_body = json.loads(stac_collection_call[1]['Body'])
            items_link = stac_collection_body['links'][0]['href']
            assert "JOB123" in items_link, f"STAC collection should point to job_id: {items_link}"
    
    def test_publisher_fallback_to_analysis_id_when_no_job_id(self):
        """Test that publisher falls back to analysis_id when job_id is not available."""
        # Create analysis without job_id
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"INCIDENTNU": "201912036"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)  # No job_id
        analysis.set_status("COMPLETED")
        analysis._raw_raster_url = "data/dummy_data/raw_dnbr.tif"
        analysis._source_vector_url = "data/dummy_data/fire.geojson"
        
        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.upload_file.return_value = None
        mock_s3_client.put_object.return_value = None
        
        # Create publisher
        publisher = S3AnalysisPublisher("test-bucket", s3_client=mock_s3_client)
        
        # Mock COG generation and file operations
        with patch.object(S3AnalysisPublisher, '_generate_cog_from_file') as mock_cog, \
             patch('os.unlink') as mock_unlink:
            mock_cog.return_value = "temp_cog.tif"
            
            # Publish analysis
            urls = publisher.publish_analysis(analysis)
            
            # Verify behavior: should fall back to analysis_id
            assert len(urls) == 2
            
            # Check that S3 uploads used analysis_id in the key
            upload_calls = mock_s3_client.upload_file.call_args_list
            analysis_id = analysis.get_id()
            
            for call in upload_calls:
                s3_key = call[0][2]  # Third argument is the key for upload_file
                assert analysis_id in s3_key, f"S3 key should contain analysis_id: {s3_key}"
                assert f"jobs/{analysis_id}/" in s3_key, f"S3 key should use analysis_id structure: {s3_key}" 