#!/usr/bin/env python3
"""
Tests for Analysis metadata structure and JSON generation.
"""

import pytest
import json
from dnbr.analysis import DNBRAnalysis
from dnbr.fire_metadata import SAFireMetadata


class TestAnalysisMetadata:
    """Test Analysis metadata structure and JSON generation."""
    
    def setup_method(self):
        """Set up test data."""
        # Create a concrete implementation for testing
        class _TestAnalysis(DNBRAnalysis):
            def _get_status(self) -> str:
                return "COMPLETED"
            
            def get(self) -> bytes:
                return b"dummy data"
        
        self.analysis = _TestAnalysis()
    
    def test_analysis_has_status_property(self):
        """Test that analysis has a status property."""
        assert hasattr(self.analysis, 'status')
        assert isinstance(self.analysis.status, str)
    
    def test_analysis_has_fire_metadata_property(self):
        """Test that analysis has fire_metadata property."""
        assert hasattr(self.analysis, 'fire_metadata')
        # Initially None, but can be set
        assert self.analysis.fire_metadata is None
    
    def test_analysis_has_raw_raster_path_property(self):
        """Test that analysis has raw_raster_path property."""
        assert hasattr(self.analysis, 'raw_raster_path')
        # Initially None, but can be set
        assert self.analysis.raw_raster_path is None
    
    def test_analysis_has_published_urls_properties(self):
        """Test that analysis has published URL properties."""
        assert hasattr(self.analysis, 'published_dnbr_raster_url')
        assert hasattr(self.analysis, 'published_vector_url')
        # Initially None, but can be set
        assert self.analysis.published_dnbr_raster_url is None
        assert self.analysis.published_vector_url is None
    
    def test_analysis_has_to_json_method(self):
        """Test that analysis has a to_json method."""
        assert hasattr(self.analysis, 'to_json')
        assert callable(self.analysis.to_json)
    
    def test_to_json_returns_valid_json(self):
        """Test that to_json returns valid JSON."""
        json_str = self.analysis.to_json()
        assert isinstance(json_str, str)
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert isinstance(data, dict)
    
    def test_json_contains_required_fields(self):
        """Test that JSON contains required fields."""
        data = json.loads(self.analysis.to_json())
        
        # Required fields
        assert 'id' in data
        assert 'status' in data
        assert 'fire_metadata' in data
        assert 'raw_raster_path' in data
        assert 'published_dnbr_raster_url' in data
        assert 'published_vector_url' in data
        
        # Field types
        assert isinstance(data['id'], str)
        assert isinstance(data['status'], str)
        assert data['fire_metadata'] is None  # Initially None
        assert data['raw_raster_path'] is None  # Initially None
        assert data['published_dnbr_raster_url'] is None  # Initially None
        assert data['published_vector_url'] is None  # Initially None
    
    def test_json_with_fire_metadata(self):
        """Test JSON structure when fire_metadata is present."""
        # Create analysis with fire metadata
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        
        data = json.loads(analysis.to_json())
        
        assert data['fire_metadata'] is not None
        assert data['fire_metadata']['provider'] == 'sa_fire'
        assert data['fire_metadata']['aoi_id'] == 'bushfire_20191230'
    
    def test_status_values(self):
        """Test that status has expected values."""
        # Status should be one of the expected values
        expected_statuses = ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED']
        assert self.analysis.status in expected_statuses
    
    def test_fire_metadata_methods(self):
        """Test fire metadata delegation methods."""
        # Without fire metadata
        assert self.analysis.get_aoi_id() is None
        assert self.analysis.get_fire_date() is None
        assert self.analysis.get_provider() is None
        
        # With fire metadata
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        
        assert analysis.get_aoi_id() == 'bushfire_20191230'
        assert analysis.get_fire_date() == '30/12/2019'
        assert analysis.get_provider() == 'sa_fire' 