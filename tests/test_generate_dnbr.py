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
    create_leaflet_map, 
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
        
        # Create a test raster file using the dummy data
        self.test_raster_path = os.path.join(self.temp_dir, "test_raster.tif")
        # Copy the dummy raster for testing
        import shutil
        shutil.copy2("data/dummy/fire_severity.tif", self.test_raster_path)
    
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
        
        # Copy the dummy raster for testing
        import shutil
        shutil.copy2("data/dummy/fire_severity.tif", raster_path)
        
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
        
        # Copy the dummy raster for testing
        import shutil
        shutil.copy2("data/dummy/fire_severity.tif", raster_path)
        
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


class TestDNBRAnalysis:
    """Test the DNBRAnalysis abstract base class and implementations."""
    
    def test_dummy_analysis_creation(self):
        """Test that DummyAnalysis can be created and has expected methods."""
        analysis = DummyAnalysis()
        
        # Test that it has the required methods
        assert hasattr(analysis, 'get_id')
        assert hasattr(analysis, 'status')
        assert hasattr(analysis, 'get')
        
        # Test that get_id returns a string
        analysis_id = analysis.get_id()
        assert isinstance(analysis_id, str)
        assert len(analysis_id) > 0
        
        # Test that status returns a string
        status = analysis.status()
        assert isinstance(status, str)
        assert status == "COMPLETED"
        
        # Test that get returns bytes
        data = analysis.get()
        assert isinstance(data, bytes)
        assert len(data) > 0
    
    def test_gee_analysis_creation(self):
        """Test that GEEAnalysis can be created and has expected methods."""
        analysis = GEEAnalysis()
        
        # Test that it has the required methods
        assert hasattr(analysis, 'get_id')
        assert hasattr(analysis, 'status')
        assert hasattr(analysis, 'get')
        
        # Test that get_id returns a string
        analysis_id = analysis.get_id()
        assert isinstance(analysis_id, str)
        assert len(analysis_id) > 0
        
        # Test that status returns a string
        status = analysis.status()
        assert isinstance(status, str)
        assert status == "SUBMITTED"
        
        # Test that get raises RuntimeError for incomplete analysis
        with pytest.raises(RuntimeError, match="not complete"):
            analysis.get()


class TestDNBRGenerators:
    """Test the DNBRGenerator implementations."""
    
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
        
        # Test that it has the required method
        assert hasattr(generator, 'generate_dnbr')
        
        # Test that it can generate an analysis
        analysis = generator.generate_dnbr(self.test_gdf)
        
        # Test that the analysis is a DummyAnalysis
        assert analysis.__class__.__name__ == 'DummyAnalysis'
        assert analysis.status() == "COMPLETED"
        
        # Test that the raster file was copied to the ULID folder
        expected_path = os.path.join(self.temp_dir, analysis.get_id(), "fire_severity.tif")
        assert os.path.exists(expected_path)
    
    def test_create_dnbr_generator_gee(self):
        """Test creating a GEE dNBR generator."""
        generator = create_dnbr_generator("gee", self.temp_dir)
        
        # Test that it has the required method
        assert hasattr(generator, 'generate_dnbr')
        
        # Test that it can generate an analysis
        analysis = generator.generate_dnbr(self.test_gdf)
        
        # Test that the analysis is a GEEAnalysis
        assert analysis.__class__.__name__ == 'GEEAnalysis'
        assert analysis.status() == "SUBMITTED"
    
    def test_create_dnbr_generator_invalid_type(self):
        """Test that creating a generator with invalid type raises error."""
        with pytest.raises(ValueError, match="Unknown dNBR generation method"):
            create_dnbr_generator("invalid_type", self.temp_dir)
    
    def test_generate_dnbr_convenience_function(self):
        """Test the generate_dnbr convenience function."""
        analysis = generate_dnbr(self.test_gdf, method="dummy")
        
        # Test that it returns a DummyAnalysis
        assert analysis.__class__.__name__ == 'DummyAnalysis'
        assert analysis.status() == "COMPLETED"
    
    def test_create_analysis_from_id_dummy(self):
        """Test creating a dummy analysis from ID."""
        analysis = create_analysis_from_id("test_id", "dummy")
        
        # Test that it's a DummyAnalysis with the correct ID
        assert analysis.__class__.__name__ == 'DummyAnalysis'
        assert analysis.get_id() == "test_id"
        assert analysis.status() == "COMPLETED"
    
    def test_create_analysis_from_id_gee(self):
        """Test creating a GEE analysis from ID."""
        analysis = create_analysis_from_id("test_id", "gee")
        
        # Test that it's a GEEAnalysis with the correct ID
        assert analysis.__class__.__name__ == 'GEEAnalysis'
        assert analysis.get_id() == "test_id"
        assert analysis.status() == "SUBMITTED"
    
    def test_create_analysis_from_id_invalid_type(self):
        """Test that creating analysis with invalid type raises error."""
        with pytest.raises(ValueError, match="Unknown generator type"):
            create_analysis_from_id("test_id", "invalid_type")


class TestIntegration:
    """Integration tests for the full pipeline."""
    
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
    
    def test_full_pipeline_functions_invoked(self):
        """Test that the full pipeline functions work together."""
        # Test the full pipeline from AOI to analysis
        analysis = generate_dnbr(self.test_gdf, method="dummy")
        
        # Verify the analysis was created
        assert analysis.__class__.__name__ == 'DummyAnalysis'
        assert analysis.status() == "COMPLETED"
        
        # Verify the data can be retrieved
        data = analysis.get()
        assert isinstance(data, bytes)
        assert len(data) > 0
        
        # Test map generation with the analysis data
        raster_path = analysis._result_path
        output_path = os.path.join(self.temp_dir, "test_map.html")
        
        map_path = create_leaflet_map(self.test_gdf, raster_path, output_path)
        
        # Verify the map was created
        assert map_path == output_path
        assert os.path.exists(output_path) 