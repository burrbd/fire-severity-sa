#!/usr/bin/env python3
"""
Tests for Analysis metadata structure and JSON generation.
"""

import pytest
import json
from dnbr.analysis import DNBRAnalysis


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
    
    def test_analysis_has_raster_urls_property(self):
        """Test that analysis has raster_urls property."""
        assert hasattr(self.analysis, 'raster_urls')
        assert isinstance(self.analysis.raster_urls, list)
    
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
        assert 'raster_urls' in data
        
        # Field types
        assert isinstance(data['id'], str)
        assert isinstance(data['status'], str)
        assert isinstance(data['raster_urls'], list)
    
    def test_raster_urls_structure(self):
        """Test that raster_urls contains expected structure."""
        data = json.loads(self.analysis.to_json())
        raster_urls = data['raster_urls']
        
        # Should be a list of URL strings
        assert isinstance(raster_urls, list)
        for url in raster_urls:
            assert isinstance(url, str)
            assert url.startswith('s3://')
    
    def test_status_values(self):
        """Test that status has expected values."""
        # Status should be one of the expected values
        expected_statuses = ['PENDING', 'RUNNING', 'COMPLETED', 'FAILED']
        assert self.analysis.status in expected_statuses 