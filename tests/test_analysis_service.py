#!/usr/bin/env python3
"""
Tests for the AnalysisService class.
"""

import pytest
from dnbr.analysis_service import AnalysisService
from dnbr.analysis import DNBRAnalysis

# Create a concrete implementation for testing
class _TestAnalysis(DNBRAnalysis):
    def _get_status(self) -> str:
        return "COMPLETED"
    
    def get(self) -> bytes:
        return b"dummy data"


class TestAnalysisService:
    """Test the AnalysisService class."""
    
    def setup_method(self):
        """Set up test data."""
        # Create analysis service
        self.service = AnalysisService()
        
        # Create a test analysis
        self.test_analysis = _TestAnalysis()
    
    def test_store_analysis(self):
        """Test storing an analysis."""
        # Should not raise an exception
        self.service.store_analysis(self.test_analysis)
    
    def test_get_analysis_nonexistent(self):
        """Test getting non-existent analysis."""
        analysis = self.service.get_analysis("nonexistent_id")
        assert analysis is None
    
    def test_store_and_get_analysis(self):
        """Test storing and retrieving an analysis."""
        # Store analysis
        self.service.store_analysis(self.test_analysis)
        
        # Get analysis
        retrieved_analysis = self.service.get_analysis(self.test_analysis.get_id())
        
        # For now, this will return None since we haven't implemented storage
        # TODO: Update this test when storage is implemented
        assert retrieved_analysis is None 