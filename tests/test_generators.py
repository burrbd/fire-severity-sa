#!/usr/bin/env python3
"""
Tests for the generator classes.
"""

import pytest
import tempfile
import shutil
import os
import geopandas as gpd
from shapely.geometry import Polygon
from dnbr.dummy_generator import DummyDNBRGenerator
from dnbr.gee_generator import GEEDNBRGenerator
from dnbr.generators import create_dnbr_generator, generate_dnbr


class TestDummyGenerator:
    """Test the DummyDNBRGenerator."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = DummyDNBRGenerator(self.temp_dir)
        
        # Create test AOI
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_aoi'}],
            crs='EPSG:4326'
        )
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_dummy_generator_initialization(self):
        """Test generator initialization."""
        assert self.generator.output_dir == self.temp_dir
    
    def test_dummy_generator_generate_dnbr(self):
        """Test dummy dNBR generation."""
        analysis = self.generator.generate_dnbr(self.test_gdf)
        
        # Check analysis properties
        assert hasattr(analysis, 'get_id')
        assert hasattr(analysis, 'status')
        assert hasattr(analysis, 'raster_urls')
        assert hasattr(analysis, 'get')
        
        # Check status
        assert analysis.status == "COMPLETED"
        
        # Check raster URLs
        assert len(analysis.raster_urls) == 2
        assert any('fire_severity.tif' in url for url in analysis.raster_urls)
        assert any('fire_severity_overlay.png' in url for url in analysis.raster_urls)
        
        # Check that get() method works
        data = analysis.get()
        assert isinstance(data, bytes)
        assert len(data) > 0


class TestGEEGenerator:
    """Test the GEEDNBRGenerator."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = GEEDNBRGenerator(self.temp_dir)
        
        # Create test AOI
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_aoi'}],
            crs='EPSG:4326'
        )
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_gee_generator_initialization(self):
        """Test generator initialization."""
        assert self.generator.output_dir == self.temp_dir
    
    def test_gee_generator_generate_dnbr(self):
        """Test GEE dNBR generation."""
        analysis = self.generator.generate_dnbr(self.test_gdf)
        
        # Check analysis properties
        assert hasattr(analysis, 'get_id')
        assert hasattr(analysis, 'status')
        assert hasattr(analysis, 'raster_urls')
        assert hasattr(analysis, 'get')
        
        # Check status
        assert analysis.status == "SUBMITTED"
        
        # Check that get() method raises error for incomplete analysis
        with pytest.raises(RuntimeError, match="GEE analysis not complete"):
            analysis.get()


class TestGeneratorFactory:
    """Test the generator factory functions."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test AOI
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        self.test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_aoi'}],
            crs='EPSG:4326'
        )
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_dummy_generator(self):
        """Test creating dummy generator."""
        generator = create_dnbr_generator("dummy", self.temp_dir)
        assert isinstance(generator, DummyDNBRGenerator)
        assert generator.output_dir == self.temp_dir
    
    def test_create_gee_generator(self):
        """Test creating GEE generator."""
        generator = create_dnbr_generator("gee", self.temp_dir)
        assert isinstance(generator, GEEDNBRGenerator)
        assert generator.output_dir == self.temp_dir
    
    def test_create_invalid_generator(self):
        """Test creating invalid generator type."""
        with pytest.raises(ValueError, match="Unknown dNBR generation method"):
            create_dnbr_generator("invalid", self.temp_dir)
    
    def test_generate_dnbr_convenience_function(self):
        """Test the generate_dnbr convenience function."""
        analysis = generate_dnbr(self.test_gdf, method="dummy")
        
        # Check analysis properties
        assert hasattr(analysis, 'get_id')
        assert hasattr(analysis, 'status')
        assert analysis.status == "COMPLETED" 