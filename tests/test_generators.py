#!/usr/bin/env python3
"""
Tests for the generators module.
"""

import pytest
from dnbr.generators import create_dnbr_generator, generate_dnbr
from dnbr.analysis import DNBRAnalysis


class TestGenerators:
    """Test the generators module functions."""
    

    
    def test_create_dnbr_generator_dummy(self):
        """Test creating dummy generator."""
        generator = create_dnbr_generator("dummy")
        assert generator is not None
        assert hasattr(generator, 'generate_dnbr')
    
    def test_dummy_generator_generate_dnbr(self):
        """Test dummy generator creates proper analysis."""
        import geopandas as gpd
        from shapely.geometry import Polygon
        
        # Create test data
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        aoi_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_fire'}],
            crs='EPSG:4326'
        )
        
        # Test generator
        generator = create_dnbr_generator("dummy")
        analysis = generator.generate_dnbr(aoi_gdf)
        
        # Verify analysis properties
        assert isinstance(analysis, DNBRAnalysis)
        assert analysis.get_id() is not None
        assert analysis.status == "PENDING"
        assert len(analysis.raster_urls) == 0  # Starts with empty URLs
    
    def test_create_dnbr_generator_invalid(self):
        """Test creating generator with invalid method."""
        with pytest.raises(ValueError, match="Unknown dNBR generation method"):
            create_dnbr_generator("invalid")
    
    def test_generate_dnbr(self):
        """Test the generate_dnbr convenience function."""
        import geopandas as gpd
        from shapely.geometry import Polygon
        
        # Create a simple test GeoDataFrame
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        aoi_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_fire'}],
            crs='EPSG:4326'
        )
        
        # Test generation
        analysis = generate_dnbr(aoi_gdf, method="dummy")
        assert isinstance(analysis, DNBRAnalysis)
        assert analysis.get_id() is not None
        assert analysis.status == "PENDING"  # Default status
        assert len(analysis.raster_urls) == 0  # Empty URLs initially
        assert analysis.get() == b""  # Default empty implementation
    
    def test_create_dnbr_generator_gee(self):
        """Test creating GEE generator."""
        generator = create_dnbr_generator("gee")
        assert generator is not None
        assert hasattr(generator, 'generate_dnbr')
    
    def test_gee_generator_generate_dnbr(self):
        """Test GEE generator creates proper analysis."""
        import geopandas as gpd
        from shapely.geometry import Polygon
        
        # Create test data
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        aoi_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_fire'}],
            crs='EPSG:4326'
        )
        
        # Test generator
        generator = create_dnbr_generator("gee")
        analysis = generator.generate_dnbr(aoi_gdf)
        
        # Verify analysis properties
        assert isinstance(analysis, DNBRAnalysis)
        assert analysis.get_id() is not None
        assert analysis.status == "PENDING"
        assert len(analysis.raster_urls) == 0
        assert analysis.generator_type == "gee" 