#!/usr/bin/env python3
"""
Tests for the generators module.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from dnbr.generators import create_dnbr_generator, generate_dnbr, generate_dnbr_batch
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
        assert analysis.status == "COMPLETED"  # Dummy generator is synchronous
        assert analysis.raw_raster_url == "data/dummy_data/raw_dnbr.tif"  # Dummy generator sets this
    
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
        
        # Verify analysis
        assert isinstance(analysis, DNBRAnalysis)
        assert analysis.get_id() is not None
        assert analysis.status == "COMPLETED"
        assert analysis.raw_raster_url == "data/dummy_data/raw_dnbr.tif"
    
    def test_generate_dnbr_batch(self):
        """Test batch processing of multiple AOIs."""
        # Create test data with multiple features
        features = [
            {
                'geometry': Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '03/12/2019',
                'INCIDENTNU': '12345'
            },
            {
                'geometry': Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '04/12/2019',
                'INCIDENTNU': '12346'
            }
        ]
        
        layer_gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        
        # Test batch generation
        analyses = generate_dnbr_batch(layer_gdf, method="dummy")
        
        # Verify results
        assert len(analyses) == 2
        assert all(isinstance(analysis, DNBRAnalysis) for analysis in analyses)
        assert all(analysis.status == "COMPLETED" for analysis in analyses)
        
        # Verify AOI IDs are extracted correctly
        aoi_ids = [analysis.get_aoi_id() for analysis in analyses]
        assert "12345" in aoi_ids
        assert "12346" in aoi_ids
    
    def test_generate_dnbr_batch_without_incident_numbers(self):
        """Test batch processing when incident numbers are not available."""
        # Create test data without incident numbers
        features = [
            {
                'geometry': Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '03/12/2019'
                # No INCIDENTNU
            },
            {
                'geometry': Polygon([(1, 1), (2, 1), (2, 2), (1, 2)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '04/12/2019'
                # No INCIDENTNU
            }
        ]
        
        layer_gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        
        # Test batch generation
        analyses = generate_dnbr_batch(layer_gdf, method="dummy")
        
        # Verify results
        assert len(analyses) == 2
        assert all(isinstance(analysis, DNBRAnalysis) for analysis in analyses)
        
        # Verify AOI IDs are generated from incident type and date
        aoi_ids = [analysis.get_aoi_id() for analysis in analyses]
        assert "bushfire_20191203" in aoi_ids
        assert "bushfire_20191204" in aoi_ids
    
    def test_generate_dnbr_batch_missing_firedate(self):
        """Test batch processing with missing FIREDATE."""
        # Create test data with missing FIREDATE
        features = [
            {
                'geometry': Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                'INCIDENTTY': 'Bushfire',
                'INCIDENTNU': '12345'
                # Missing FIREDATE
            }
        ]
        
        layer_gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        
        # Test batch generation should fail
        with pytest.raises(ValueError, match="FIREDATE property is required"):
            generate_dnbr_batch(layer_gdf, method="dummy") 