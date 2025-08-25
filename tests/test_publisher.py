#!/usr/bin/env python3
"""
Tests for the AnalysisPublisher class.
"""

import pytest
from unittest.mock import MagicMock
from dnbr.publisher import AnalysisPublisher, S3AnalysisPublisher, create_publisher
from dnbr.analysis import DNBRAnalysis


class TestAnalysisPublisher:
    """Test the AnalysisPublisher abstract base class."""
    
    def test_analysis_publisher_is_abstract(self):
        """Test that AnalysisPublisher cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AnalysisPublisher()


class TestS3AnalysisPublisher:
    """Test the S3AnalysisPublisher implementation."""
    
    def setup_method(self):
        """Set up test data."""
        self.publisher = S3AnalysisPublisher("test-bucket", "us-west-2")
        
        # Create a concrete implementation for testing
        class _TestAnalysis(DNBRAnalysis):
            def _get_status(self) -> str:
                return "COMPLETED"
            
            def get(self) -> bytes:
                return b"dummy_raster_data"
        
        self.completed_analysis = _TestAnalysis()
        
        # Create an incomplete analysis
        class _IncompleteAnalysis(DNBRAnalysis):
            def _get_status(self) -> str:
                return "RUNNING"
            
            def get(self) -> bytes:
                return b"dummy_data"
        
        self.incomplete_analysis = _IncompleteAnalysis()
    
    def test_s3_publisher_initialization(self):
        """Test S3 publisher initialization."""
        assert self.publisher.bucket_name == "test-bucket"
        assert self.publisher.region == "us-west-2"
    
    def test_publish_completed_analysis(self):
        """Test publishing a completed analysis."""
        urls = self.publisher.publish_analysis(self.completed_analysis)
        
        # Should return S3 URLs
        assert isinstance(urls, list)
        assert len(urls) == 2
        
        # Check URL format
        analysis_id = self.completed_analysis.get_id()
        expected_urls = [
            f"s3://test-bucket/analyses/{analysis_id}/fire_severity.tif",
            f"s3://test-bucket/analyses/{analysis_id}/fire_severity_overlay.png"
        ]
        assert urls == expected_urls
    
    def test_process_raster_data_exists(self):
        """Test that _process_raster_data method exists."""
        assert hasattr(self.publisher, '_process_raster_data')
        assert callable(self.publisher._process_raster_data)
    
    def test_publish_incomplete_analysis_raises_error(self):
        """Test that publishing incomplete analysis raises error."""
        with pytest.raises(ValueError, match="Cannot publish incomplete analysis"):
            self.publisher.publish_analysis(self.incomplete_analysis)
    
    def test_publish_analysis_with_get_failure(self):
        """Test publishing when analysis.get() fails."""
        # Create analysis that raises error on get()
        class _FailingAnalysis(DNBRAnalysis):
            def _get_status(self) -> str:
                return "COMPLETED"
            
            def get(self) -> bytes:
                raise RuntimeError("Data retrieval failed")
        
        failing_analysis = _FailingAnalysis()
        
        # Currently the shell implementation doesn't call analysis.get(),
        # so it should succeed and return dummy URLs
        urls = self.publisher.publish_analysis(failing_analysis)
        assert isinstance(urls, list)
        assert len(urls) == 2


class TestCreatePublisher:
    """Test the create_publisher factory function."""
    
    def test_create_s3_publisher(self):
        """Test creating S3 publisher with factory function."""
        publisher = create_publisher("s3", bucket_name="my-bucket", region="eu-west-1")
        
        assert isinstance(publisher, S3AnalysisPublisher)
        assert publisher.bucket_name == "my-bucket"
        assert publisher.region == "eu-west-1"
    
    def test_create_s3_publisher_defaults(self):
        """Test creating S3 publisher with default values."""
        publisher = create_publisher("s3")
        
        assert isinstance(publisher, S3AnalysisPublisher)
        assert publisher.bucket_name == "fire-severity-analyses"
        assert publisher.region == "us-east-1"
    
    def test_create_invalid_publisher_raises_error(self):
        """Test that creating invalid publisher type raises error."""
        with pytest.raises(ValueError, match="Unknown publisher type"):
            create_publisher("invalid_type")


class TestPublisherIntegration:
    """Test publisher integration with analysis objects."""
    
    def test_publisher_with_analysis_metadata(self):
        """Test that publisher works with analysis metadata."""
        # Create a concrete implementation for testing
        class _TestAnalysis(DNBRAnalysis):
            def _get_status(self) -> str:
                return "COMPLETED"
            
            def get(self) -> bytes:
                return b"test_raster_data"
        
        analysis = _TestAnalysis()
        publisher = S3AnalysisPublisher("test-bucket")
        
        # Publish the analysis
        urls = publisher.publish_analysis(analysis)
        
        # Verify the URLs contain the analysis ID
        analysis_id = analysis.get_id()
        assert any(analysis_id in url for url in urls)
        
        # Verify the URLs point to the correct bucket
        assert all("test-bucket" in url for url in urls) 