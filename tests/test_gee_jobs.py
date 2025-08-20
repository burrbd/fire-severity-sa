"""
Tests for GEE job management and tracking.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import geopandas as gpd
from shapely.geometry import Polygon
from botocore.exceptions import ClientError

from src.gee_jobs import (
    generate_ulid,
    setup_gee_authentication,
    submit_gee_dnbr_job,
    update_job_tracking,
    get_job_status,
    list_pending_jobs,
    get_current_commit_hash,
    verify_gee_connection
)


class TestGenerateULID:
    def test_generate_ulid_returns_string(self):
        """Test that generate_ulid returns a string."""
        ulid = generate_ulid()
        assert isinstance(ulid, str)
        assert len(ulid) == 26  # ULIDs are 26 characters long
        assert ulid.startswith("01")  # ULIDs start with timestamp

    def test_generate_ulid_unique(self):
        """Test that generate_ulid returns unique values."""
        ulid1 = generate_ulid()
        ulid2 = generate_ulid()
        assert ulid1 != ulid2
        assert len(ulid1) == 26  # ULIDs are 26 characters long


class TestGEEAuthentication:
    def test_setup_gee_authentication_returns_bool(self):
        """Test that setup_gee_authentication returns a boolean."""
        result = setup_gee_authentication()
        assert isinstance(result, bool)

    def test_verify_gee_connection_returns_bool(self):
        """Test that verify_gee_connection returns a boolean."""
        result = verify_gee_connection()
        assert isinstance(result, bool)


class TestJobSubmission:
    def test_submit_gee_dnbr_job_returns_job_id(self):
        """Test that submit_gee_dnbr_job returns a job ID."""
        # Create a simple mock AOI
        geometry = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        aoi_gdf = gpd.GeoDataFrame([{'geometry': geometry}])
        
        job_id = submit_gee_dnbr_job("test_fire", aoi_gdf)
        assert isinstance(job_id, str)
        assert len(job_id) == 26  # ULIDs are 26 characters long


class TestJobTracking:
    def test_update_job_tracking_noop(self):
        """Test that update_job_tracking works as noop function."""
        # Should not raise any exceptions
        update_job_tracking("test_job_123", "test_fire", "abc123")
        # Function should complete successfully (it just prints)

    def test_get_job_status_returns_mock_status(self):
        """Test that get_job_status returns mock status."""
        status = get_job_status("test_job_123")
        assert status == "SUBMITTED"  # Mock response from noop function

    def test_list_pending_jobs_returns_empty_list(self):
        """Test that list_pending_jobs returns empty list (noop)."""
        pending_jobs = list_pending_jobs()
        assert pending_jobs == []  # Mock empty response from noop function


class TestGitIntegration:
    @patch('subprocess.run')
    def test_get_current_commit_hash_success(self, mock_run):
        """Test that get_current_commit_hash returns commit hash."""
        mock_run.return_value.stdout = "abc123def456\n"
        mock_run.return_value.returncode = 0
        
        commit_hash = get_current_commit_hash()
        assert commit_hash == "abc123def456"
        mock_run.assert_called_once_with(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True
        )

    @patch('subprocess.run')
    def test_get_current_commit_hash_failure(self, mock_run):
        """Test that get_current_commit_hash handles git failure."""
        mock_run.side_effect = Exception("Git command failed")
        
        commit_hash = get_current_commit_hash()
        assert commit_hash == "unknown" 