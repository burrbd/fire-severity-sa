#!/usr/bin/env python3
"""
Tests for FireMetadata filename generation functionality.
"""

import pytest
from dnbr.fire_metadata import SAFireMetadata, create_fire_metadata_from_feature


class TestFireMetadataFilenameGeneration:
    """Test FireMetadata filename generation functionality."""
    
    def test_generate_filename_raster(self):
        """Test generating raster filename."""
        metadata = SAFireMetadata("Bushfire", "03/12/2019", {"INCIDENTNU": "12345"})
        filename = metadata.generate_filename("raster")
        assert filename == "12345_dnbr.cog.tif"
    
    def test_generate_filename_vector(self):
        """Test generating vector filename."""
        metadata = SAFireMetadata("Bushfire", "03/12/2019", {"INCIDENTNU": "12345"})
        filename = metadata.generate_filename("vector")
        assert filename == "12345_aoi.geojson"
    
    def test_generate_filename_other(self):
        """Test generating other filename types."""
        metadata = SAFireMetadata("Bushfire", "03/12/2019", {"INCIDENTNU": "12345"})
        filename = metadata.generate_filename("metadata")
        assert filename == "12345_metadata"
    
    def test_generate_filename_without_incident_number(self):
        """Test generating filename when incident number is not available."""
        metadata = SAFireMetadata("Bushfire", "03/12/2019", {})
        filename = metadata.generate_filename("raster")
        assert filename == "bushfire_20191203_dnbr.cog.tif"
    
    def test_create_fire_metadata_from_feature_dict(self):
        """Test creating metadata from feature dict."""
        feature = {
            'properties': {
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '03/12/2019',
                'INCIDENTNU': '12345'
            }
        }
        metadata = create_fire_metadata_from_feature(feature)
        assert isinstance(metadata, SAFireMetadata)
        assert metadata.get_id() == "12345"
        assert metadata.generate_filename("raster") == "12345_dnbr.cog.tif"
    
    def test_create_fire_metadata_from_feature_pandas_series(self):
        """Test creating metadata from pandas Series."""
        import pandas as pd
        
        # Create a mock pandas Series
        feature = pd.Series({
            'INCIDENTTY': 'Bushfire',
            'FIREDATE': '03/12/2019',
            'INCIDENTNU': '12345'
        })
        
        metadata = create_fire_metadata_from_feature(feature)
        assert isinstance(metadata, SAFireMetadata)
        assert metadata.get_id() == "12345"
        assert metadata.generate_filename("vector") == "12345_aoi.geojson"
    
    def test_create_fire_metadata_from_feature_missing_firedate(self):
        """Test creating metadata with missing FIREDATE."""
        feature = {
            'properties': {
                'INCIDENTTY': 'Bushfire',
                'INCIDENTNU': '12345'
                # Missing FIREDATE
            }
        }
        
        with pytest.raises(ValueError, match="FIREDATE property is required"):
            create_fire_metadata_from_feature(feature)

