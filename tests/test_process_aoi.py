#!/usr/bin/env python3
"""
Tests for process_aoi.py - Fire Severity Mapping AOI Processor

This test suite focuses on ensuring functions are invoked correctly rather than
testing the dummy data generation logic.
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

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from process_aoi import (
    load_aoi, 
    generate_dnbr_raster, 
    create_leaflet_map, 
    calculate_dnbr_values,
    generate_dnbr_raster_tile,
    create_dnbr_colormap,
    create_raster_overlay_image,
    main
)


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


class TestCalculateDNBRValues:
    """Test the calculate_dnbr_values function."""
    
    def setup_method(self):
        """Set up test data."""
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
    
    def test_calculate_dnbr_values_invoked(self):
        """Test that calculate_dnbr_values function is invoked and returns expected structure."""
        dnbr_values, bounds = calculate_dnbr_values(self.test_gdf)
        
        # Verify function returns expected types and shapes
        assert isinstance(dnbr_values, np.ndarray)
        assert dnbr_values.shape == (50, 50)  # Default size
        assert isinstance(bounds, np.ndarray)  # total_bounds returns numpy array
        assert len(bounds) == 4  # minx, miny, maxx, maxy
    
    def test_calculate_dnbr_values_custom_size(self):
        """Test that calculate_dnbr_values accepts custom dimensions."""
        dnbr_values, bounds = calculate_dnbr_values(self.test_gdf, width=100, height=75)
        
        assert dnbr_values.shape == (75, 100)
        assert isinstance(bounds, np.ndarray)  # total_bounds returns numpy array
        assert len(bounds) == 4


class TestGenerateDNBRRasterTile:
    """Test the generate_dnbr_raster_tile function."""
    
    def setup_method(self):
        """Set up test data."""
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
        self.temp_dir = tempfile.mkdtemp()
        self.test_dnbr_values = np.random.random((50, 50))
        self.test_bounds = (0, 0, 1, 1)
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_generate_dnbr_raster_tile_invoked(self):
        """Test that generate_dnbr_raster_tile function is invoked and creates file."""
        output_path = os.path.join(self.temp_dir, "test_raster.tif")
        
        result_path = generate_dnbr_raster_tile(
            self.test_dnbr_values, 
            self.test_bounds, 
            self.test_gdf, 
            output_path
        )
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        
        # Verify the raster file can be opened and has expected properties
        with rasterio.open(output_path) as src:
            assert src.count == 1
            assert src.dtypes[0] == 'float32'
            assert src.nodata == -9999
    
    def test_generate_dnbr_raster_tile_creates_directory(self):
        """Test that the function creates output directory if it doesn't exist."""
        output_path = os.path.join(self.temp_dir, "new_dir", "test_raster.tif")
        
        result_path = generate_dnbr_raster_tile(
            self.test_dnbr_values, 
            self.test_bounds, 
            self.test_gdf, 
            output_path
        )
        
        assert result_path == output_path
        assert os.path.exists(output_path)
        assert os.path.exists(os.path.dirname(output_path))


class TestCreateDNBRColormap:
    """Test the create_dnbr_colormap function."""
    
    def test_create_dnbr_colormap_invoked(self):
        """Test that create_dnbr_colormap function is invoked and returns colormap."""
        colormap = create_dnbr_colormap()
        
        # Verify function returns a matplotlib colormap
        assert hasattr(colormap, 'N')  # Number of colors
        assert hasattr(colormap, '__call__')  # Callable for color mapping


class TestCreateRasterOverlayImage:
    """Test the create_raster_overlay_image function."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
        
        # Create a test raster file
        self.test_raster_path = os.path.join(self.temp_dir, "test_raster.tif")
        test_dnbr_values = np.random.random((50, 50))
        test_bounds = (0, 0, 1, 1)
        generate_dnbr_raster_tile(test_dnbr_values, test_bounds, self.test_gdf, self.test_raster_path)
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_raster_overlay_image_invoked(self):
        """Test that create_raster_overlay_image function is invoked and creates overlay."""
        output_path = os.path.join(self.temp_dir, "test_overlay.png")
        
        overlay_path, bounds = create_raster_overlay_image(self.test_raster_path, output_path)
        
        assert overlay_path == output_path
        assert os.path.exists(output_path)
        assert isinstance(bounds, rasterio.coords.BoundingBox)


class TestGenerateDNBRRaster:
    """Test the generate_dnbr_raster function."""
    
    def setup_method(self):
        """Set up test data."""
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('process_aoi.calculate_dnbr_values')
    @patch('process_aoi.generate_dnbr_raster_tile')
    def test_generate_dnbr_raster_orchestrates_functions(self, mock_generate_tile, mock_calculate_values):
        """Test that generate_dnbr_raster orchestrates the other functions correctly."""
        # Mock return values
        mock_dnbr_values = np.random.random((50, 50))
        mock_bounds = (0, 0, 1, 1)
        mock_calculate_values.return_value = (mock_dnbr_values, mock_bounds)
        
        output_path = os.path.join(self.temp_dir, "test_raster.tif")
        mock_generate_tile.return_value = output_path
        
        result_path = generate_dnbr_raster(self.test_gdf, output_path)
        
        # Verify functions were called correctly
        mock_calculate_values.assert_called_once_with(self.test_gdf)
        mock_generate_tile.assert_called_once_with(mock_dnbr_values, mock_bounds, self.test_gdf, output_path)
        assert result_path == output_path
    
    def test_generate_dnbr_raster_creates_file(self):
        """Test that generate_dnbr_raster creates the expected output file."""
        output_path = os.path.join(self.temp_dir, "test_raster.tif")
        
        result_path = generate_dnbr_raster(self.test_gdf, output_path)
        
        assert result_path == output_path
        assert os.path.exists(output_path)


class TestCreateLeafletMap:
    """Test the create_leaflet_map function."""
    
    def setup_method(self):
        """Set up test data."""
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test'}],
            crs='EPSG:4326'
        )
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('process_aoi.create_raster_overlay_image')
    def test_create_leaflet_map_invokes_overlay_function(self, mock_create_overlay):
        """Test that create_leaflet_map invokes the overlay creation function."""
        raster_path = os.path.join(self.temp_dir, "dummy_raster.tif")
        output_path = os.path.join(self.temp_dir, "test_map.html")
        
        # Create a dummy raster file for the test
        test_dnbr_values = np.random.random((50, 50))
        test_bounds = (0, 0, 1, 1)
        generate_dnbr_raster_tile(test_dnbr_values, test_bounds, self.test_gdf, raster_path)
        
        # Mock overlay function to actually create the overlay file
        mock_overlay_path = os.path.join(self.temp_dir, "test_overlay.png")
        mock_bounds = rasterio.coords.BoundingBox(0, 0, 1, 1)
        
        # Create a dummy overlay image file
        import matplotlib.pyplot as plt
        plt.figure(figsize=(10, 10))
        plt.imshow(np.random.random((50, 50)))
        plt.axis('off')
        plt.savefig(mock_overlay_path, bbox_inches='tight', pad_inches=0, transparent=True, dpi=150)
        plt.close()
        
        mock_create_overlay.return_value = (mock_overlay_path, mock_bounds)
        
        result_path = create_leaflet_map(self.test_gdf, raster_path, output_path)
        
        # Verify overlay function was called
        mock_create_overlay.assert_called_once_with(raster_path)
        assert result_path == output_path
        assert os.path.exists(output_path)
    
    def test_create_leaflet_map_creates_directory(self):
        """Test that the function creates output directory if it doesn't exist."""
        raster_path = os.path.join(self.temp_dir, "dummy_raster.tif")
        output_path = os.path.join(self.temp_dir, "new_dir", "test_map.html")
        
        # Create a dummy raster file for the test
        test_dnbr_values = np.random.random((50, 50))
        test_bounds = (0, 0, 1, 1)
        generate_dnbr_raster_tile(test_dnbr_values, test_bounds, self.test_gdf, raster_path)
        
        # Verify the output directory doesn't exist yet
        assert not os.path.exists(os.path.dirname(output_path))
        
        # Let the function create the directory and files
        result_path = create_leaflet_map(self.test_gdf, raster_path, output_path)
        
        # Verify the function created everything as expected
        assert result_path == output_path
        assert os.path.exists(output_path)
        assert os.path.exists(os.path.dirname(output_path))
        
        # Verify the overlay image was also created in the same directory
        overlay_path = os.path.join(os.path.dirname(output_path), "fire_severity_overlay.png")
        assert os.path.exists(overlay_path)


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
    
    @patch('process_aoi.generate_dnbr_raster')
    @patch('process_aoi.create_leaflet_map')
    def test_main_invokes_functions(self, mock_create_map, mock_generate_raster):
        """Test that main function invokes the expected functions."""
        mock_generate_raster.return_value = "test_raster.tif"
        mock_create_map.return_value = "test_map.html"
        
        with patch('sys.argv', ['process_aoi.py', self.test_geojson]):
            with patch('builtins.print') as mock_print:
                main()
                
                # Verify functions were called
                mock_generate_raster.assert_called_once()
                mock_create_map.assert_called_once()
                
                # Check that the function printed success messages
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("Processing AOI:" in call for call in print_calls)
                assert any("Loaded AOI with" in call for call in print_calls)
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
    
    def test_full_pipeline_functions_invoked(self):
        """Test that the complete pipeline invokes all expected functions."""
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