#!/usr/bin/env python3
"""
Tests for DNBRAnalysis class with FireMetadata integration.
"""

import pytest
import json
from unittest.mock import Mock, patch
from dnbr.analysis import DNBRAnalysis
from dnbr.fire_metadata import SAFireMetadata


class TestDNBRAnalysis:
    """Test the DNBRAnalysis class."""
    
    def test_analysis_creation_without_metadata(self):
        """Test creating analysis without fire metadata."""
        analysis = DNBRAnalysis(generator_type="dummy")
        
        assert analysis.generator_type == "dummy"
        assert analysis.fire_metadata is None
        assert analysis.get_aoi_id() is None
        assert analysis.get_fire_date() is None
        assert analysis.get_provider() is None
        assert analysis.status == "PENDING"
        assert analysis.raw_raster_path is None
        assert analysis.published_dnbr_raster_url is None
        assert analysis.published_vector_url is None
    
    def test_analysis_creation_with_metadata(self):
        """Test creating analysis with fire metadata."""
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(generator_type="dummy", fire_metadata=fire_metadata)
        
        assert analysis.generator_type == "dummy"
        assert analysis.fire_metadata == fire_metadata
        assert analysis.get_aoi_id() == "bushfire_20191230"
        assert analysis.get_fire_date() == "30/12/2019"
        assert analysis.get_provider() == "sa_fire"
    
    def test_analysis_id_generation(self):
        """Test that analysis gets a unique ULID."""
        analysis1 = DNBRAnalysis()
        analysis2 = DNBRAnalysis()
        
        assert analysis1.get_id() != analysis2.get_id()
        assert len(analysis1.get_id()) > 0
    
    def test_status_management(self):
        """Test status setting and getting."""
        analysis = DNBRAnalysis()
        
        assert analysis.get_status() == "PENDING"
        assert analysis.status == "PENDING"
        
        analysis.set_status("COMPLETED")
        assert analysis.get_status() == "COMPLETED"
        assert analysis.status == "COMPLETED"
    
    def test_created_at_timestamp(self):
        """Test that created_at timestamp is set."""
        analysis = DNBRAnalysis()
        
        assert analysis.get_created_at() is not None
        assert len(analysis.get_created_at()) > 0
    
    def test_raw_raster_path_property(self):
        """Test raw_raster_path property access."""
        analysis = DNBRAnalysis()
        
        # Initially None
        assert analysis.raw_raster_path is None
        
        # Set and get
        analysis._raw_raster_path = "test/path.tif"
        assert analysis.raw_raster_path == "test/path.tif"
    
    def test_published_urls_properties(self):
        """Test published URL properties."""
        analysis = DNBRAnalysis()
        
        # Initially None
        assert analysis.published_dnbr_raster_url is None
        assert analysis.published_vector_url is None
        
        # Set and get
        analysis._published_dnbr_raster_url = "s3://bucket/file.tif"
        analysis._published_vector_url = "s3://bucket/file.geojson"
        
        assert analysis.published_dnbr_raster_url == "s3://bucket/file.tif"
        assert analysis.published_vector_url == "s3://bucket/file.geojson"
    
    def test_get_method_default(self):
        """Test the default get() method returns empty bytes."""
        analysis = DNBRAnalysis()
        assert analysis.get() == b""
    
    def test_to_json_without_metadata(self):
        """Test JSON serialization without fire metadata."""
        analysis = DNBRAnalysis(generator_type="dummy")
        analysis._raw_raster_path = "test/path.tif"
        
        json_str = analysis.to_json()
        data = json.loads(json_str)
        
        assert data["generator_type"] == "dummy"
        assert data["fire_metadata"] is None
        assert data["status"] == "PENDING"
        assert data["raw_raster_path"] == "test/path.tif"
        assert data["published_dnbr_raster_url"] is None
        assert data["published_vector_url"] is None
        assert "id" in data
        assert "created_at" in data
    
    def test_to_json_with_metadata(self):
        """Test JSON serialization with fire metadata."""
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(generator_type="dummy", fire_metadata=fire_metadata)
        analysis._raw_raster_path = "test/path.tif"
        analysis._published_dnbr_raster_url = "s3://bucket/file.tif"
        analysis._published_vector_url = "s3://bucket/file.geojson"
        
        json_str = analysis.to_json()
        data = json.loads(json_str)
        
        assert data["generator_type"] == "dummy"
        assert data["fire_metadata"]["provider"] == "sa_fire"
        assert data["fire_metadata"]["aoi_id"] == "bushfire_20191230"
        assert data["status"] == "PENDING"
        assert data["raw_raster_path"] == "test/path.tif"
        assert data["published_dnbr_raster_url"] == "s3://bucket/file.tif"
        assert data["published_vector_url"] == "s3://bucket/file.geojson"
    
    def test_from_json_without_metadata(self):
        """Test JSON deserialization without fire metadata."""
        original_analysis = DNBRAnalysis(generator_type="dummy")
        original_analysis._raw_raster_path = "test/path.tif"
        original_analysis.set_status("COMPLETED")
        
        json_str = original_analysis.to_json()
        reconstructed_analysis = DNBRAnalysis.from_json(json_str)
        
        assert reconstructed_analysis.generator_type == original_analysis.generator_type
        assert reconstructed_analysis.fire_metadata is None
        assert reconstructed_analysis.get_id() == original_analysis.get_id()
        assert reconstructed_analysis.status == original_analysis.status
        assert reconstructed_analysis.raw_raster_path == original_analysis.raw_raster_path
        assert reconstructed_analysis.published_dnbr_raster_url is None
        assert reconstructed_analysis.published_vector_url is None
    
    def test_from_json_with_metadata(self):
        """Test JSON deserialization with fire metadata."""
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        original_analysis = DNBRAnalysis(generator_type="dummy", fire_metadata=fire_metadata)
        original_analysis._raw_raster_path = "test/path.tif"
        original_analysis._published_dnbr_raster_url = "s3://bucket/file.tif"
        original_analysis._published_vector_url = "s3://bucket/file.geojson"
        
        json_str = original_analysis.to_json()
        reconstructed_analysis = DNBRAnalysis.from_json(json_str)
        
        assert reconstructed_analysis.generator_type == original_analysis.generator_type
        assert reconstructed_analysis.get_aoi_id() == original_analysis.get_aoi_id()
        assert reconstructed_analysis.get_fire_date() == original_analysis.get_fire_date()
        assert reconstructed_analysis.get_provider() == original_analysis.get_provider()
        assert reconstructed_analysis.get_id() == original_analysis.get_id()
        assert reconstructed_analysis.raw_raster_path == original_analysis.raw_raster_path
        assert reconstructed_analysis.published_dnbr_raster_url == original_analysis.published_dnbr_raster_url
        assert reconstructed_analysis.published_vector_url == original_analysis.published_vector_url
    
    def test_from_json_with_unknown_provider(self):
        """Test JSON deserialization with unknown fire metadata provider."""
        json_data = {
            "id": "test-id",
            "generator_type": "dummy",
            "fire_metadata": {
                "provider": "unknown_provider",
                "aoi_id": "test",
                "fire_date": "30/12/2019"
            },
            "status": "PENDING",
            "created_at": "2023-01-01T00:00:00",
            "raw_raster_path": None,
            "published_dnbr_raster_url": None,
            "published_vector_url": None
        }
        
        json_str = json.dumps(json_data)
        
        with pytest.raises(ValueError, match="Unknown fire metadata provider"):
            DNBRAnalysis.from_json(json_str)
    
    def test_from_json_missing_fields(self):
        """Test JSON deserialization with missing fields."""
        json_data = {
            "generator_type": "dummy"
            # Missing other fields
        }
        
        json_str = json.dumps(json_data)
        analysis = DNBRAnalysis.from_json(json_str)
        
        # Should use defaults for missing fields
        assert analysis.generator_type == "dummy"
        assert analysis.fire_metadata is None
        assert analysis.status == "PENDING"
        assert analysis.raw_raster_path is None
    
    def test_fire_metadata_property_access(self):
        """Test accessing fire metadata properties."""
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        analysis = DNBRAnalysis(fire_metadata=fire_metadata)
        
        # Test property access
        assert analysis.fire_metadata == fire_metadata
        
        # Test method access
        assert analysis.get_aoi_id() == "bushfire_20191230"
        assert analysis.get_fire_date() == "30/12/2019"
        assert analysis.get_provider() == "sa_fire"
    
    def test_fire_metadata_methods_without_metadata(self):
        """Test fire metadata methods when no metadata is present."""
        analysis = DNBRAnalysis()
        
        assert analysis.get_aoi_id() is None
        assert analysis.get_fire_date() is None
        assert analysis.get_provider() is None
    
    @patch('dnbr.analysis.ulid')
    def test_ulid_generation(self, mock_ulid):
        """Test ULID generation in analysis creation."""
        mock_ulid.ULID.return_value = "01K33HZPY7ZSXN7CTR8JQ7JBG5"
        
        analysis = DNBRAnalysis()
        
        assert analysis.get_id() == "01K33HZPY7ZSXN7CTR8JQ7JBG5"
        mock_ulid.ULID.assert_called_once()





class TestDNBRAnalysisIntegration:
    """Integration tests for DNBRAnalysis."""
    
    def test_full_analysis_lifecycle(self):
        """Test the full lifecycle of creating, modifying, and serializing analysis."""
        # Create fire metadata
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        
        # Create analysis
        analysis = DNBRAnalysis(generator_type="dummy", fire_metadata=fire_metadata)
        
        # Modify analysis
        analysis.set_status("COMPLETED")
        analysis._raw_raster_path = "test/path.tif"
        analysis._published_dnbr_raster_url = "s3://bucket/file.tif"
        analysis._published_vector_url = "s3://bucket/file.geojson"
        
        # Serialize
        json_str = analysis.to_json()
        
        # Deserialize
        reconstructed_analysis = DNBRAnalysis.from_json(json_str)
        
        # Verify all properties are preserved
        assert reconstructed_analysis.generator_type == analysis.generator_type
        assert reconstructed_analysis.get_aoi_id() == analysis.get_aoi_id()
        assert reconstructed_analysis.get_fire_date() == analysis.get_fire_date()
        assert reconstructed_analysis.get_provider() == analysis.get_provider()
        assert reconstructed_analysis.get_id() == analysis.get_id()
        assert reconstructed_analysis.status == analysis.status
        assert reconstructed_analysis.raw_raster_path == analysis.raw_raster_path
        assert reconstructed_analysis.published_dnbr_raster_url == analysis.published_dnbr_raster_url
        assert reconstructed_analysis.published_vector_url == analysis.published_vector_url
    
    def test_analysis_with_different_generator_types(self):
        """Test analysis with different generator types."""
        fire_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        
        # Test dummy generator
        dummy_analysis = DNBRAnalysis(generator_type="dummy", fire_metadata=fire_metadata)
        assert dummy_analysis.generator_type == "dummy"
        
        # Test GEE generator
        gee_analysis = DNBRAnalysis(generator_type="gee", fire_metadata=fire_metadata)
        assert gee_analysis.generator_type == "gee"
        
        # Test unknown generator
        unknown_analysis = DNBRAnalysis(generator_type="unknown", fire_metadata=fire_metadata)
        assert unknown_analysis.generator_type == "unknown"
    
    def test_analysis_status_transitions(self):
        """Test analysis status transitions."""
        analysis = DNBRAnalysis()
        
        # Initial state
        assert analysis.status == "PENDING"
        
        # Transition to RUNNING
        analysis.set_status("RUNNING")
        assert analysis.status == "RUNNING"
        
        # Transition to COMPLETED
        analysis.set_status("COMPLETED")
        assert analysis.status == "COMPLETED"
        
        # Transition to FAILED
        analysis.set_status("FAILED")
        assert analysis.status == "FAILED"
