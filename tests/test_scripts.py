#!/usr/bin/env python3
"""
Tests for the script modules used by GitHub Actions.
Simplified for the new clean job-based architecture.
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

from scripts.dnbr_analysis_job import main as dnbr_analysis_job_main
from scripts.publish_dnbr_job import main as publish_dnbr_job_main, publish_dnbr_data


class TestDNBRAnalysisJobScript:
    """Test the dnbr_analysis_job.py script."""
    
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
    
    @patch('sys.argv', ['dnbr_analysis_job.py', 'data/fire.geojson', 'dummy'])
    @patch('scripts.dnbr_analysis_job.load_aoi')
    @patch('scripts.dnbr_analysis_job.create_job')
    @patch('scripts.dnbr_analysis_job.create_job_service')
    def test_dnbr_analysis_job_success(self, mock_create_service, mock_create_job, mock_load_aoi):
        """Test successful dNBR job execution."""
        # Mock the job and analyses
        mock_job = MagicMock()
        mock_job.get_id.return_value = "test_job_id"
        mock_job.get_analysis_count.return_value = 2
        mock_job.get_completed_analyses.return_value = [MagicMock(), MagicMock()]
        mock_job.get_pending_analyses.return_value = []
        mock_job.get_failed_analyses.return_value = []
        mock_job.get_analyses.return_value = [MagicMock(), MagicMock()]
        
        # Mock the job creation and execution
        mock_create_job.return_value = mock_job
        mock_job.execute.return_value = mock_job
        
        # Mock the AOI loading
        mock_gdf = MagicMock()
        mock_gdf.__len__ = lambda x: 2
        mock_load_aoi.return_value = mock_gdf
        
        # Mock the job service
        mock_service = MagicMock()
        mock_create_service.return_value = mock_service
        
        # Test the main function
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            dnbr_analysis_job_main()
        
        # Verify the functions were called correctly
        mock_load_aoi.assert_called_once_with('data/fire.geojson')
        mock_create_job.assert_called_once_with('dummy', mock_gdf, provider='sa_fire')
        mock_job.execute.assert_called_once()
        mock_create_service.assert_called_once()
        mock_service.store_job.assert_called_once_with(mock_job)
    
    @patch('sys.argv', ['dnbr_analysis_job.py'])
    def test_dnbr_analysis_job_no_arguments(self):
        """Test script with no arguments."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                dnbr_analysis_job_main()
        
        assert exc_info.value.code == 1


class TestPublishDNBRJobScript:
    """Test the publish_dnbr_job.py script."""
    
    @patch('sys.argv', ['publish_dnbr_job.py'])
    def test_publish_dnbr_job_no_arguments(self):
        """Test script with no arguments."""
        with patch('sys.stdout', new=MagicMock()) as mock_stdout:
            with pytest.raises(SystemExit) as exc_info:
                publish_dnbr_job_main()
        
        assert exc_info.value.code == 2  # argparse error code
