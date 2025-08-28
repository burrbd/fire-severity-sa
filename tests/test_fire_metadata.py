#!/usr/bin/env python3
"""
Tests for FireMetadata architecture.
"""

import pytest
import json
import tempfile
import os
from unittest.mock import patch, mock_open
from dnbr.fire_metadata import FireMetadata, SAFireMetadata, create_fire_metadata


class TestFireMetadata:
    """Test the abstract FireMetadata base class."""
    
    def test_fire_metadata_is_abstract(self):
        """Test that FireMetadata cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FireMetadata()


class TestSAFireMetadata:
    """Test the SAFireMetadata concrete implementation."""
    
    def test_sa_fire_metadata_creation(self):
        """Test creating SAFireMetadata with valid data."""
        metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        
        assert metadata.incident_type == "Bushfire"
        assert metadata.fire_date == "30/12/2019"
        assert metadata.raw_properties == {"test": "data"}
        assert metadata.get_provider() == "sa_fire"
    
    def test_fire_id_generation_valid_date(self):
        """Test fire ID generation with valid date format."""
        metadata = SAFireMetadata("Bushfire", "30/12/2019", {})
        fire_id = metadata.get_id()
        
        assert fire_id == "bushfire_20191230"
    
    def test_fire_id_generation_invalid_date(self):
        """Test fire ID generation with invalid date format."""
        metadata = SAFireMetadata("Bushfire", "invalid-date", {})
        fire_id = metadata.get_id()
        
        # Should extract numbers from invalid date (but there are none)
        assert "bushfire_" in fire_id
        assert fire_id == "bushfire_"  # No numbers in "invalid-date"
    
    def test_fire_id_generation_special_characters(self):
        """Test fire ID generation with special characters in incident type."""
        metadata = SAFireMetadata("Bush Fire!", "30/12/2019", {})
        fire_id = metadata.get_id()
        
        # Should sanitize special characters (space and exclamation both become underscores)
        assert fire_id == "bush_fire__20191230"
    
    def test_get_date(self):
        """Test getting the fire date."""
        metadata = SAFireMetadata("Bushfire", "30/12/2019", {})
        assert metadata.get_date() == "30/12/2019"
    
    def test_get_provider(self):
        """Test getting the provider name."""
        metadata = SAFireMetadata("Bushfire", "30/12/2019", {})
        assert metadata.get_provider() == "sa_fire"
    
    def test_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        data = metadata.to_dict()
        
        assert data["fire_id"] == "bushfire_20191230"
        assert data["fire_date"] == "30/12/2019"
        assert data["provider"] == "sa_fire"
        assert data["provider_metadata"]["incident_type"] == "Bushfire"
        assert data["provider_metadata"]["raw_properties"] == {"test": "data"}
    
    def test_from_dict(self):
        """Test creating metadata from dictionary."""
        data = {
            "fire_id": "bushfire_20191230",
            "fire_date": "30/12/2019",
            "provider": "sa_fire",
            "provider_metadata": {
                "incident_type": "Bushfire",
                "raw_properties": {"test": "data"}
            }
        }
        
        metadata = SAFireMetadata.from_dict(data)
        
        assert metadata.incident_type == "Bushfire"
        assert metadata.fire_date == "30/12/2019"
        assert metadata.raw_properties == {"test": "data"}
        assert metadata.get_id() == "bushfire_20191230"
    
    def test_from_dict_missing_fields(self):
        """Test creating metadata from dictionary with missing fields."""
        data = {
            "fire_date": "30/12/2019",
            "provider_metadata": {}
        }
        
        metadata = SAFireMetadata.from_dict(data)
        
        assert metadata.incident_type == "Unknown"
        assert metadata.fire_date == "30/12/2019"
        assert metadata.raw_properties == {}
    
    def test_from_geojson_valid(self):
        """Test creating metadata from valid GeoJSON file."""
        geojson_data = {
            "features": [{
                "properties": {
                    "INCIDENTTY": "Bushfire",
                    "FIREDATE": "30/12/2019",
                    "other": "data"
                }
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            json.dump(geojson_data, f)
            geojson_path = f.name
        
        try:
            metadata = SAFireMetadata.from_geojson(geojson_path)
            
            assert metadata.incident_type == "Bushfire"
            assert metadata.fire_date == "30/12/2019"
            assert metadata.get_id() == "bushfire_20191230"
            assert "other" in metadata.raw_properties
        finally:
            os.unlink(geojson_path)
    
    def test_from_geojson_missing_features(self):
        """Test creating metadata from GeoJSON with missing features."""
        geojson_data = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            json.dump(geojson_data, f)
            geojson_path = f.name
        
        try:
            with pytest.raises(ValueError, match="No features found in GeoJSON"):
                SAFireMetadata.from_geojson(geojson_path)
        finally:
            os.unlink(geojson_path)
    
    def test_from_geojson_missing_firedate(self):
        """Test creating metadata from GeoJSON with missing FIREDATE."""
        geojson_data = {
            "features": [{
                "properties": {
                    "INCIDENTTY": "Bushfire"
                    # Missing FIREDATE
                }
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            json.dump(geojson_data, f)
            geojson_path = f.name
        
        try:
            with pytest.raises(ValueError, match="FIREDATE property is required"):
                SAFireMetadata.from_geojson(geojson_path)
        finally:
            os.unlink(geojson_path)
    
    def test_from_geojson_file_not_found(self):
        """Test creating metadata from non-existent GeoJSON file."""
        with pytest.raises(FileNotFoundError):
            SAFireMetadata.from_geojson("nonexistent.geojson")
    
    def test_from_geojson_invalid_json(self):
        """Test creating metadata from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            f.write("invalid json content")
            geojson_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON in file"):
                SAFireMetadata.from_geojson(geojson_path)
        finally:
            os.unlink(geojson_path)


class TestFireMetadataFactory:
    """Test the FireMetadata factory methods."""
    
    def test_from_json_data_sa_fire(self):
        """Test creating FireMetadata from JSON data for SA Fire."""
        data = {
            "fire_id": "bushfire_20191230",
            "fire_date": "30/12/2019",
            "provider": "sa_fire",
            "provider_metadata": {
                "incident_type": "Bushfire",
                "raw_properties": {"test": "data"}
            }
        }
        
        metadata = FireMetadata.from_json_data(data)
        
        assert isinstance(metadata, SAFireMetadata)
        assert metadata.get_id() == "bushfire_20191230"
        assert metadata.get_provider() == "sa_fire"
    
    def test_from_json_data_unknown_provider(self):
        """Test creating FireMetadata from JSON data with unknown provider."""
        data = {
            "provider": "unknown_provider"
        }
        
        with pytest.raises(ValueError, match="Unknown fire metadata provider"):
            FireMetadata.from_json_data(data)
    
    def test_from_json_data_missing_provider(self):
        """Test creating FireMetadata from JSON data with missing provider."""
        data = {}
        
        with pytest.raises(ValueError, match="Unknown fire metadata provider"):
            FireMetadata.from_json_data(data)
    
    def test_create_fire_metadata_sa_fire_with_path(self):
        """Test creating fire metadata for SA Fire with GeoJSON path."""
        geojson_data = {
            "features": [{
                "properties": {
                    "INCIDENTTY": "Bushfire",
                    "FIREDATE": "30/12/2019"
                }
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            json.dump(geojson_data, f)
            geojson_path = f.name
        
        try:
            metadata = create_fire_metadata("sa_fire", geojson_path=geojson_path)
            
            assert isinstance(metadata, SAFireMetadata)
            assert metadata.get_id() == "bushfire_20191230"
        finally:
            os.unlink(geojson_path)
    
    def test_create_fire_metadata_sa_fire_missing_path(self):
        """Test creating fire metadata for SA Fire without GeoJSON path."""
        with pytest.raises(ValueError, match="geojson_path is required for sa_fire provider"):
            create_fire_metadata("sa_fire")
    
    def test_create_fire_metadata_unknown_provider(self):
        """Test creating fire metadata with unknown provider."""
        with pytest.raises(ValueError, match="Unknown fire metadata provider"):
            create_fire_metadata("unknown_provider")


class TestFireMetadataIntegration:
    """Integration tests for FireMetadata."""
    
    def test_full_metadata_lifecycle(self):
        """Test the full lifecycle of creating, serializing, and deserializing metadata."""
        # Create metadata
        original_metadata = SAFireMetadata("Bushfire", "30/12/2019", {"test": "data"})
        
        # Serialize to dict
        data = original_metadata.to_dict()
        
        # Deserialize from dict
        reconstructed_metadata = SAFireMetadata.from_dict(data)
        
        # Verify they're equivalent
        assert original_metadata.get_id() == reconstructed_metadata.get_id()
        assert original_metadata.get_date() == reconstructed_metadata.get_date()
        assert original_metadata.get_provider() == reconstructed_metadata.get_provider()
        assert original_metadata.incident_type == reconstructed_metadata.incident_type
        assert original_metadata.raw_properties == reconstructed_metadata.raw_properties
    
    def test_factory_method_integration(self):
        """Test integration between factory methods."""
        # Create using factory
        geojson_data = {
            "features": [{
                "properties": {
                    "INCIDENTTY": "Bushfire",
                    "FIREDATE": "30/12/2019"
                }
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            json.dump(geojson_data, f)
            geojson_path = f.name
        
        try:
            metadata1 = create_fire_metadata("sa_fire", geojson_path=geojson_path)
            
            # Serialize and deserialize using factory
            data = metadata1.to_dict()
            metadata2 = FireMetadata.from_json_data(data)
            
            # Verify they're equivalent
            assert metadata1.get_id() == metadata2.get_id()
            assert metadata1.get_provider() == metadata2.get_provider()
        finally:
            os.unlink(geojson_path)

