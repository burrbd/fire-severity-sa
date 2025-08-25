#!/usr/bin/env python3
"""
Tests for the new dNBR analysis architecture.
Simplified for the clean architecture.
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open, call
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
import rasterio
import folium

# Add the project root to the path so we can import the modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.generate_dnbr_utils import (
    load_aoi, 
    create_leaflet_map, 
    create_dnbr_colormap,
    create_raster_overlay_image
)
from dnbr.analysis import DNBRAnalysis


class TestLoadAOI:
    """Test the load_aoi function."""
    
    def test_load_aoi_success(self):
        """Test successful loading of a valid GeoJSON file."""
        # Create a temporary GeoJSON file
        geojson_data = {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
                },
                "properties": {"name": "test_aoi"}
            }]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            import json
            json.dump(geojson_data, f)
            temp_file = f.name
        
        try:
            gdf = load_aoi(temp_file)
            assert isinstance(gdf, gpd.GeoDataFrame)
            assert len(gdf) == 1
            assert gdf.crs is not None
        finally:
            os.unlink(temp_file)
    
    def test_load_aoi_file_not_found(self):
        """Test loading a non-existent file."""
        with pytest.raises(SystemExit) as exc_info:
            load_aoi("nonexistent_file.geojson")
        assert exc_info.value.code == 1
    
    def test_load_aoi_invalid_geojson(self):
        """Test loading an invalid GeoJSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name
        
        try:
            with pytest.raises(SystemExit) as exc_info:
                load_aoi(temp_file)
            assert exc_info.value.code == 1
        finally:
            os.unlink(temp_file)


class TestCreateDNBRColormap:
    """Test the create_dnbr_colormap function."""
    
    def test_create_dnbr_colormap_invoked(self):
        """Test that create_dnbr_colormap function is invoked and returns colormap."""
        colormap = create_dnbr_colormap()
        
        # Should return a matplotlib colormap
        assert colormap is not None
        # Test that it can be called with values
        assert callable(colormap)





class TestCreateLeafletMap:
    """Test the create_leaflet_map function."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test AOI
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_aoi'}],
            crs='EPSG:4326'
        )
        
        # Create test raster
        self.raster_path = os.path.join(self.temp_dir, "test_raster.tif")
        with rasterio.open(
            self.raster_path,
            'w',
            driver='GTiff',
            height=10,
            width=10,
            count=1,
            dtype=rasterio.uint8,
            crs='EPSG:4326',
            transform=rasterio.transform.from_bounds(0, 0, 1, 1, 10, 10)
        ) as dst:
            data = np.random.randint(0, 255, (1, 10, 10), dtype=np.uint8)
            dst.write(data)
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_leaflet_map_success(self):
        """Test successful creation of Leaflet map."""
        output_path = os.path.join(self.temp_dir, "test_map.html")
        
        # Test the function
        create_leaflet_map(self.test_gdf, self.raster_path, output_path)
        
        # Check that output file was created
        assert os.path.exists(output_path)
        
        # Check that it's an HTML file
        assert output_path.endswith('.html')
        
        # Check that it contains expected content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'leaflet' in content.lower()
            assert 'map' in content.lower()


class TestAnalysisMetadata:
    """Test the new analysis metadata structure."""
    
    def test_analysis_metadata_structure(self):
        """Test that analysis objects have the expected metadata structure."""
        # Create a concrete implementation for testing
        class _TestAnalysis(DNBRAnalysis):
            def _get_status(self) -> str:
                return "COMPLETED"
            
            def get(self) -> bytes:
                return b"dummy data"
        
        analysis = _TestAnalysis()
        
        # Test core properties
        assert hasattr(analysis, 'get_id')
        assert hasattr(analysis, 'status')
        assert hasattr(analysis, 'raster_urls')
        assert hasattr(analysis, 'to_json')
        
        # Test property types
        assert isinstance(analysis.get_id(), str)
        assert isinstance(analysis.status, str)
        assert isinstance(analysis.raster_urls, list)
        
        # Test JSON serialization
        json_str = analysis.to_json()
        assert isinstance(json_str, str)
        
        import json
        data = json.loads(json_str)
        assert 'id' in data
        assert 'status' in data
        assert 'raster_urls' in data 