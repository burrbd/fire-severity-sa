#!/usr/bin/env python3
"""
Tests for the script modules used by GitHub Actions.
Simplified for the new clean architecture.
"""

import pytest
import tempfile
import shutil
import os
import sys
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import Polygon

# Add the project root to the path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_dnbr_analysis import main as generate_dnbr_analysis_main
from scripts.publish_dnbr_analysis import main as publish_dnbr_analysis_main, publish_dnbr_data
from scripts.generate_map_shell import main as generate_map_shell_main
from dnbr.analysis import DNBRAnalysis


class TestGenerateDNBRAnalysisScript:
    """Test the generate_dnbr_analysis.py script."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.aoi_path = os.path.join(self.temp_dir, "test_fire.geojson")
        
        # Create a test GeoJSON file
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_fire'}],
            crs='EPSG:4326'
        )
        test_gdf.to_file(self.aoi_path, driver='GeoJSON')
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('sys.argv', ['generate_dnbr_analysis.py', 'data/fire.geojson', 'dummy'])
    @patch('scripts.generate_dnbr_analysis.load_aoi')
    @patch('scripts.generate_dnbr_analysis.generate_dnbr')
    @patch('scripts.generate_dnbr_analysis.create_analysis_service')
    def test_generate_dnbr_analysis_success(self, mock_create_service, mock_generate_dnbr, mock_load_aoi):
        """Test successful dNBR generation."""
        # Mock the analysis object
        mock_analysis = MagicMock()
        mock_analysis.get_id.return_value = "test_analysis_id"
        mock_analysis.status = "COMPLETED"  # Property, not method
        mock_generate_dnbr.return_value = mock_analysis
        
        # Mock the AOI loading
        mock_gdf = MagicMock()
        mock_gdf.__len__ = lambda x: 1
        mock_load_aoi.return_value = mock_gdf
        
        # Mock the analysis service
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service
        
        # Test the main function
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            generate_dnbr_analysis_main()
        
        # Verify the functions were called correctly
        mock_load_aoi.assert_called_once_with('data/fire.geojson')
        mock_generate_dnbr.assert_called_once_with(mock_gdf, method='dummy', data_path='data/fire.geojson', fire_metadata=None)
        mock_create_service.assert_called_once()
        mock_service.store_analysis.assert_called_once_with(mock_analysis)
    
    @patch('sys.argv', ['generate_dnbr_analysis.py', 'data/fire.geojson', 'dummy'])
    @patch('scripts.generate_dnbr_analysis.load_aoi')
    def test_generate_dnbr_analysis_load_aoi_failure(self, mock_load_aoi):
        """Test script when AOI loading fails."""
        mock_load_aoi.side_effect = Exception("File not found")
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    @patch('sys.argv', ['generate_dnbr_analysis.py', 'data/fire.geojson', 'dummy'])
    @patch('scripts.generate_dnbr_analysis.load_aoi')
    @patch('scripts.generate_dnbr_analysis.generate_dnbr')
    def test_generate_dnbr_analysis_generation_failure(self, mock_generate_dnbr, mock_load_aoi):
        """Test script when analysis generation fails."""
        # Mock successful AOI loading
        mock_gdf = MagicMock()
        mock_gdf.__len__ = lambda x: 1
        mock_load_aoi.return_value = mock_gdf
        
        # Mock failed analysis generation
        mock_generate_dnbr.side_effect = Exception("Generation failed")
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    @patch('sys.argv', ['generate_dnbr_analysis.py', 'data/fire.geojson', 'dummy'])
    @patch('scripts.generate_dnbr_analysis.load_aoi')
    @patch('scripts.generate_dnbr_analysis.generate_dnbr')
    @patch('scripts.generate_dnbr_analysis.create_analysis_service')
    def test_generate_dnbr_analysis_storage_failure(self, mock_create_service, mock_generate_dnbr, mock_load_aoi):
        """Test script when DynamoDB storage fails."""
        # Mock successful AOI loading
        mock_gdf = MagicMock()
        mock_gdf.__len__ = lambda x: 1
        mock_load_aoi.return_value = mock_gdf
        
        # Mock successful analysis generation
        mock_analysis = MagicMock()
        mock_analysis.get_id.return_value = "test_analysis_id"
        mock_analysis.status = "PENDING"
        mock_generate_dnbr.return_value = mock_analysis
        
        # Mock failed service creation
        mock_create_service.side_effect = Exception("Service creation failed")
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    @patch('sys.argv', ['generate_dnbr_analysis.py'])
    def test_generate_dnbr_analysis_no_arguments(self):
        """Test script with no arguments."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1  # script error code


class TestPublishDNBRAnalysisScript:
    """Test the publish_dnbr_analysis.py script."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.aoi_path = os.path.join(self.temp_dir, "test_fire.geojson")
        
        # Create a test GeoJSON file
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_fire'}],
            crs='EPSG:4326'
        )
        test_gdf.to_file(self.aoi_path, driver='GeoJSON')
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('sys.argv', ['publish_dnbr_analysis.py'])
    def test_publish_dnbr_analysis_no_arguments(self):
        """Test script with no arguments."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                publish_dnbr_analysis_main()
        
        assert exc_info.value.code == 2  # argparse error code


class TestGenerateMapShellScript:
    """Test the generate_map_shell.py script."""
    
    def setup_method(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        self.aoi_path = os.path.join(self.temp_dir, "test_fire.geojson")
        
        # Create a test GeoJSON file
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        test_gdf = gpd.GeoDataFrame(
            [{'geometry': geometry, 'name': 'test_fire'}],
            crs='EPSG:4326'
        )
        test_gdf.to_file(self.aoi_path, driver='GeoJSON')
    
    def teardown_method(self):
        """Clean up test data."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('sys.argv', ['generate_map_shell.py', 'data/fire.geojson'])
    @patch('scripts.generate_map_shell.generate_leaflet_map_standalone')
    def test_generate_map_shell_success(self, mock_generate_map):
        """Test successful map generation."""
        # Mock map generation
        mock_generate_map.return_value = "test_map.html"
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            generate_map_shell_main()
        
        # Verify the function was called correctly
        mock_generate_map.assert_called_once_with('data/fire.geojson')
    
    @patch('sys.argv', ['generate_map_shell.py'])
    def test_generate_map_shell_no_arguments(self):
        """Test script with no arguments."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_map_shell_main()
        
        assert exc_info.value.code == 2  # argparse error code


class TestAnalysisIntegration:
    """Test integration with the new analysis system."""
    
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
        assert hasattr(analysis, 'fire_metadata')
        assert hasattr(analysis, 'raw_raster_path')
        assert hasattr(analysis, 'published_dnbr_raster_url')
        assert hasattr(analysis, 'published_vector_url')
        assert hasattr(analysis, 'to_json')
        
        # Test property types
        assert isinstance(analysis.get_id(), str)
        assert isinstance(analysis.status, str)
        assert analysis.fire_metadata is None  # Initially None
        assert analysis.raw_raster_path is None  # Initially None
        assert analysis.published_dnbr_raster_url is None  # Initially None
        assert analysis.published_vector_url is None  # Initially None
        
        # Test JSON serialization
        json_str = analysis.to_json()
        assert isinstance(json_str, str)
        
        import json
        data = json.loads(json_str)
        assert 'id' in data
        assert 'status' in data
        assert 'fire_metadata' in data
        assert 'raw_raster_path' in data
        assert 'published_dnbr_raster_url' in data
        assert 'published_vector_url' in data 