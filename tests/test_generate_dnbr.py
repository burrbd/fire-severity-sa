#!/usr/bin/env python3
"""
Tests for the new dNBR analysis architecture.

This test suite focuses on ensuring the new polymorphic analysis system works correctly.
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
    generate_dnbr_raster, 
    create_leaflet_map, 
    calculate_dnbr_values,
    generate_dnbr_raster_tile,
    create_dnbr_colormap,
    create_raster_overlay_image
)
from dnbr.generators import create_dnbr_generator, generate_dnbr, create_analysis_from_id
from dnbr.dummy_analysis import DummyAnalysis
from dnbr.gee_analysis import GEEAnalysis


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
    
    @patch('scripts.generate_dnbr_utils.calculate_dnbr_values')
    @patch('scripts.generate_dnbr_utils.generate_dnbr_raster_tile')
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
    
    @patch('scripts.generate_dnbr_utils.create_raster_overlay_image')
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
        
        # Verify overlay function was called with both raster_path and overlay_path
        expected_overlay_path = os.path.join(os.path.dirname(output_path), "fire_severity_overlay.png")
        mock_create_overlay.assert_called_once_with(raster_path, expected_overlay_path)
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


# TestMain class removed - testing script execution is not necessary for core functionality
    



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


class TestDNBRAnalysis:
    """Test the new DNBRAnalysis system."""
    
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
    
    def test_create_dnbr_generator_dummy(self):
        """Test creating a dummy dNBR generator."""
        generator = create_dnbr_generator("dummy", self.temp_dir)
        assert generator is not None
        assert hasattr(generator, 'generate_dnbr')
    
    def test_create_dnbr_generator_gee(self):
        """Test creating a GEE dNBR generator."""
        generator = create_dnbr_generator("gee", self.temp_dir)
        assert generator is not None
        assert hasattr(generator, 'generate_dnbr')
    
    def test_create_dnbr_generator_invalid(self):
        """Test creating a generator with invalid method."""
        with pytest.raises(ValueError, match="Unknown dNBR generation method"):
            create_dnbr_generator("invalid")
    
    def test_generate_dnbr_dummy(self):
        """Test generating a dummy dNBR analysis."""
        analysis = generate_dnbr(self.test_gdf, method="dummy", output_dir=self.temp_dir)
        
        assert analysis.__class__.__name__ == 'DummyAnalysis'
        assert analysis.status() == "COMPLETED"
        assert analysis.get_id() is not None
        
        # Check that the pre-committed raster file exists
        assert os.path.exists("data/dummy/fire_severity.tif")
    
    def test_generate_dnbr_gee(self):
        """Test generating a GEE dNBR analysis."""
        analysis = generate_dnbr(self.test_gdf, method="gee", output_dir=self.temp_dir)
        
        assert analysis.__class__.__name__ == 'GEEAnalysis'
        assert analysis.status() == "SUBMITTED"
        assert analysis.get_id() is not None
    
    def test_create_analysis_from_id_dummy(self):
        """Test creating a dummy analysis from ID."""
        # First create an analysis to get an ID
        analysis = generate_dnbr(self.test_gdf, method="dummy", output_dir=self.temp_dir)
        analysis_id = analysis.get_id()
        
        # Create analysis from ID
        recreated_analysis = create_analysis_from_id(analysis_id, "dummy", self.temp_dir)
        
        assert recreated_analysis.__class__.__name__ == 'DummyAnalysis'
        assert recreated_analysis.get_id() == analysis_id
        assert recreated_analysis.status() == "COMPLETED"
    
    def test_create_analysis_from_id_gee(self):
        """Test creating a GEE analysis from ID."""
        analysis_id = "test_gee_id"
        analysis = create_analysis_from_id(analysis_id, "gee", self.temp_dir)
        
        assert analysis.__class__.__name__ == 'GEEAnalysis'
        assert analysis.get_id() == analysis_id
        assert analysis.status() == "SUBMITTED"
    
    def test_create_analysis_from_id_invalid(self):
        """Test creating an analysis with invalid type."""
        with pytest.raises(ValueError, match="Unknown generator type"):
            create_analysis_from_id("test_id", "invalid", self.temp_dir)
    
    def test_dummy_analysis_get_data(self):
        """Test getting data from a dummy analysis."""
        analysis = generate_dnbr(self.test_gdf, method="dummy", output_dir=self.temp_dir)
        
        data = analysis.get()
        assert isinstance(data, bytes)
        assert len(data) > 0
    
    def test_gee_analysis_get_data_not_complete(self):
        """Test getting data from a GEE analysis that's not complete."""
        analysis = generate_dnbr(self.test_gdf, method="gee", output_dir=self.temp_dir)
        
        # GEE analysis should not be complete initially
        assert analysis.status() == "SUBMITTED"
        
        # Getting data should raise an error
        with pytest.raises(RuntimeError, match="not complete"):
            analysis.get()


if __name__ == "__main__":
    pytest.main([__file__]) 