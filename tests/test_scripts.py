#!/usr/bin/env python3
"""
Tests for the script modules used by GitHub Actions.
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
from scripts.download_dnbr_analysis import main as download_dnbr_analysis_main, download_dnbr_data
from scripts.generate_map_shell import main as generate_map_shell_main
from dnbr.generators import create_analysis_from_id
from dnbr.dummy_analysis import DummyAnalysis


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
    def test_generate_dnbr_analysis_success(self, mock_generate_dnbr, mock_load_aoi):
        """Test successful dNBR generation."""
        # Mock the analysis object
        mock_analysis = MagicMock()
        mock_analysis.get_id.return_value = "test_analysis_id"
        mock_analysis.status.return_value = "COMPLETED"
        mock_generate_dnbr.return_value = mock_analysis
        
        # Mock the AOI loading
        mock_gdf = MagicMock()
        mock_gdf.__len__ = lambda x: 1
        mock_load_aoi.return_value = mock_gdf
        
        # Test the main function
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            generate_dnbr_analysis_main()
        
        # Verify the functions were called correctly
        mock_load_aoi.assert_called_once_with('data/fire.geojson')
        mock_generate_dnbr.assert_called_once_with(mock_gdf, method='dummy')
    
    @patch('sys.argv', ['generate_dnbr_analysis.py'])
    def test_generate_dnbr_analysis_no_arguments(self):
        """Test script with no arguments."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    @patch('sys.argv', ['generate_dnbr_analysis.py', 'nonexistent.geojson'])
    @patch('scripts.generate_dnbr_analysis.load_aoi')
    def test_generate_dnbr_analysis_invalid_aoi(self, mock_load_aoi):
        """Test script with invalid AOI file."""
        mock_load_aoi.side_effect = FileNotFoundError("File not found")
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    @patch('sys.argv', ['generate_dnbr_analysis.py', 'data/fire.geojson', 'dummy'])
    @patch('scripts.generate_dnbr_analysis.load_aoi')
    @patch('scripts.generate_dnbr_analysis.generate_dnbr')
    def test_generate_dnbr_analysis_generation_failure(self, mock_generate_dnbr, mock_load_aoi):
        """Test script when dNBR generation fails."""
        # Mock the AOI loading
        mock_gdf = MagicMock()
        mock_gdf.__len__ = lambda x: 1
        mock_load_aoi.return_value = mock_gdf
        
        # Mock generation failure
        mock_generate_dnbr.side_effect = Exception("Generation failed")
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_dnbr_analysis_main()
        
        assert exc_info.value.code == 1


class TestDownloadDNBRAnalysisScript:
    """Test the download_dnbr_analysis.py script."""
    
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
    
    @patch('sys.argv', ['download_dnbr_analysis.py', '--analysis-id', 'test_id', '--generator-type', 'dummy'])
    @patch('scripts.download_dnbr_analysis.create_analysis_from_id')
    @patch('scripts.generate_dnbr_utils.create_raster_overlay_image')
    def test_download_dnbr_analysis_success(self, mock_create_overlay, mock_create_analysis):
        """Test successful data download."""
        # Mock the analysis object
        mock_analysis = MagicMock()
        mock_analysis.status.return_value = "COMPLETED"
        mock_analysis.get.return_value = b"dummy_data"
        mock_analysis.get_id.return_value = "test_id"
        mock_create_analysis.return_value = mock_analysis
        
        # Mock the overlay creation
        mock_create_overlay.return_value = ("test_overlay.png", (0, 0, 1, 1))
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            download_dnbr_analysis_main()
        
        # Verify the functions were called correctly
        mock_create_analysis.assert_called_once_with('test_id', 'dummy')
        mock_create_overlay.assert_called_once()
    
    @patch('sys.argv', ['download_dnbr_analysis.py', '--analysis-id', 'test_id', '--generator-type', 'dummy'])
    @patch('scripts.download_dnbr_analysis.create_analysis_from_id')
    def test_download_dnbr_analysis_incomplete_analysis(self, mock_create_analysis):
        """Test download with incomplete analysis."""
        # Mock the analysis object with incomplete status
        mock_analysis = MagicMock()
        mock_analysis.status.return_value = "RUNNING"
        mock_create_analysis.return_value = mock_analysis
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                download_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    @patch('sys.argv', ['download_dnbr_analysis.py', '--analysis-id', 'test_id', '--generator-type', 'dummy'])
    @patch('scripts.download_dnbr_analysis.create_analysis_from_id')
    def test_download_dnbr_analysis_get_failure(self, mock_create_analysis):
        """Test download when data retrieval fails."""
        # Mock the analysis object
        mock_analysis = MagicMock()
        mock_analysis.status.return_value = "COMPLETED"
        mock_analysis.get.side_effect = Exception("Data retrieval failed")
        mock_create_analysis.return_value = mock_analysis
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                download_dnbr_analysis_main()
        
        assert exc_info.value.code == 1
    
    def test_download_dnbr_analysis_function(self):
        """Test the download_dnbr_data function directly."""
        with patch('scripts.download_dnbr_analysis.create_analysis_from_id') as mock_create_analysis:
            with patch('scripts.generate_dnbr_utils.create_raster_overlay_image') as mock_create_overlay:
                # Mock the analysis object
                mock_analysis = MagicMock()
                mock_analysis.status.return_value = "COMPLETED"
                mock_analysis.get.return_value = b"dummy_data"
                mock_analysis.get_id.return_value = "test_id"
                mock_create_analysis.return_value = mock_analysis
                
                # Mock the overlay creation
                mock_create_overlay.return_value = ("test_overlay.png", (0, 0, 1, 1))
                
                # Test the function
                download_dnbr_data("test_id", "dummy", self.aoi_path)
                
                # Verify calls
                mock_create_analysis.assert_called_once_with("test_id", "dummy")
                mock_create_overlay.assert_called_once()


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
    
    @patch('sys.argv', ['generate_map_shell.py', 'data/fire.geojson'])
    @patch('scripts.generate_map_shell.generate_leaflet_map_standalone')
    def test_generate_map_shell_generation_failure(self, mock_generate_map):
        """Test script when map generation fails."""
        # Mock generation failure
        mock_generate_map.side_effect = Exception("Map generation failed")
        
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                generate_map_shell_main()
        
        assert exc_info.value.code == 1


class TestScriptIntegration:
    """Test integration between scripts and the analysis system."""
    
    def test_create_analysis_from_id_dummy(self):
        """Test that create_analysis_from_id works with dummy analysis."""
        analysis = create_analysis_from_id("test_id", "dummy")
        
        assert isinstance(analysis, DummyAnalysis)
        assert analysis.get_id() == "test_id"
        assert analysis.status() == "COMPLETED"
    
    def test_create_analysis_from_id_invalid_type(self):
        """Test that create_analysis_from_id raises error for invalid type."""
        with pytest.raises(ValueError, match="Unknown generator type"):
            create_analysis_from_id("test_id", "invalid_type") 