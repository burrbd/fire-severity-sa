#!/usr/bin/env python3
"""
Tests for process_aoi.py - Fire Severity Mapping AOI Processor

This test suite aims for 100% coverage of the process_aoi.py module.
"""

import pytest
import sys
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon
import rasterio
import folium

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from process_aoi import load_aoi, generate_dnbr_raster, create_leaflet_map, main


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


class TestGenerateDNBRRaster:
    """Test the generate_dnbr_raster function."""
    
    def setup_method(self):
        """Set up test data."""
        # Create a simple test GeoDataFrame
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_dnbr_raster_success(self):
        """Test successful generation of dNBR raster."""
        output_path = os.path.join(self.temp_dir, "test_raster.tif")
        
        result_path = generate_dnbr_raster(self.test_gdf, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verify the raster file can be opened and has expected properties
        with rasterio.open(output_path) as src:
            assert src.count == 1
            assert src.dtypes[0] == 'float64'
            assert src.nodata == -9999
    
    def test_generate_dnbr_raster_creates_directory(self):
        """Test that the function creates output directory if it doesn't exist."""
        output_path = os.path.join(self.temp_dir, "new_dir", "test_raster.tif")
        
        result_path = generate_dnbr_raster(self.test_gdf, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        assert os.path.exists(os.path.dirname(output_path))
    
    def test_generate_dnbr_raster_severity_values(self):
        """Test that the generated raster has reasonable severity values."""
        output_path = os.path.join(self.temp_dir, "test_raster.tif")
        
        generate_dnbr_raster(self.test_gdf, output_path)
        
        with rasterio.open(output_path) as src:
            data = src.read(1)
            # Check that values are within expected range (0-4)
            assert np.min(data) >= 0
            assert np.max(data) <= 4
            # Check that we have some variation (not all same value)
            assert np.std(data) > 0


class TestCreateLeafletMap:
    """Test the create_leaflet_map function."""
    
    def setup_method(self):
        """Set up test data."""
        # Create a simple test GeoDataFrame
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_leaflet_map_success(self):
        """Test successful creation of Leaflet map."""
        raster_path = os.path.join(self.temp_dir, "dummy_raster.tif")
        output_path = os.path.join(self.temp_dir, "test_map.html")
        
        # Create a dNBR raster file first
        generate_dnbr_raster(self.test_gdf, raster_path)
        
        result_path = create_leaflet_map(self.test_gdf, raster_path, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verify the HTML file contains expected content
        with open(output_path, 'r') as f:
            content = f.read()
            assert 'folium' in content
    
    def test_create_leaflet_map_creates_directory(self):
        """Test that the function creates output directory if it doesn't exist."""
        raster_path = os.path.join(self.temp_dir, "dummy_raster.tif")
        output_path = os.path.join(self.temp_dir, "new_dir", "test_map.html")
        
        # Create a dNBR raster file first
        generate_dnbr_raster(self.test_gdf, raster_path)
        
        result_path = create_leaflet_map(self.test_gdf, raster_path, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        assert os.path.exists(os.path.dirname(output_path))


class TestMain:
    """Test the main function."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test GeoJSON file
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
        
        self.test_geojson = os.path.join(self.temp_dir, "test_aoi.geojson")
        with open(self.test_geojson, 'w') as f:
            import json
            json.dump(geojson_data, f)
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_main_success(self):
        """Test successful execution of main function."""
        with patch('sys.argv', ['process_aoi.py', self.test_geojson]):
            with patch('builtins.print') as mock_print:
                main()
                
                # Check that the function printed success messages
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("Processing AOI:" in call for call in print_calls)
                assert any("Loaded AOI with" in call for call in print_calls)
                assert any("Generated dNBR raster:" in call for call in print_calls)
                assert any("Generated Leaflet map:" in call for call in print_calls)
                assert any("✅ Steel thread pipeline completed successfully!" in call for call in print_calls)
    
    def test_main_no_arguments(self):
        """Test main function with no arguments."""
        with patch('sys.argv', ['process_aoi.py']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    def test_main_too_many_arguments(self):
        """Test main function with too many arguments."""
        with patch('sys.argv', ['process_aoi.py', 'arg1', 'arg2']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
    
    def test_main_invalid_aoi_file(self):
        """Test main function with invalid AOI file."""
        with patch('sys.argv', ['process_aoi.py', 'nonexistent_file.geojson']):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1


class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a test GeoJSON file
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
        
        self.test_geojson = os.path.join(self.temp_dir, "test_aoi.geojson")
        with open(self.test_geojson, 'w') as f:
            import json
            json.dump(geojson_data, f)
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_full_pipeline(self):
        """Test the complete pipeline from AOI to outputs."""
        # Load AOI
        aoi_gdf = load_aoi(self.test_geojson)
        assert isinstance(aoi_gdf, gpd.GeoDataFrame)
        assert len(aoi_gdf) == 1
        
        # Generate raster
        raster_path = os.path.join(self.temp_dir, "fire_severity.tif")
        result_raster = generate_dnbr_raster(aoi_gdf, raster_path)
        assert os.path.exists(result_raster)
        
        # Create map
        map_path = os.path.join(self.temp_dir, "fire_severity_map.html")
        result_map = create_leaflet_map(aoi_gdf, result_raster, map_path)
        assert os.path.exists(result_map)
        
        # Verify outputs are valid
        with rasterio.open(result_raster) as src:
            assert src.count == 1
        
        with open(result_map, 'r') as f:
            content = f.read()
            assert 'folium' in content


if __name__ == "__main__":
    pytest.main([__file__]) 