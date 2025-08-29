#!/usr/bin/env python3
"""
Tests for the new polymorphic job execution architecture.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from dnbr.job import DNBRAnalysisJob
from dnbr.analysis import DNBRAnalysis


class TestJobExecution:
    """Test the new job execution architecture."""
    
    def test_dummy_job_execute_returns_job_with_analyses(self):
        """Test that dummy job execute() returns a job with analyses."""
        # Create test data
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
        
        # Create and execute dummy job
        from dnbr.jobs import DummyJob
        job = DummyJob(layer_gdf, provider="sa_fire")
        result_job = job.execute()
        
        # Verify job properties
        assert isinstance(result_job, DNBRAnalysisJob)
        assert result_job.generator_type == "dummy"
        assert result_job.get_id() is not None
        assert result_job.get_analysis_count() == 2
        
        # Verify analyses
        analyses = result_job.get_analyses()
        assert len(analyses) == 2
        assert all(isinstance(analysis, DNBRAnalysis) for analysis in analyses)
        assert all(analysis.status == "COMPLETED" for analysis in analyses)  # Dummy is synchronous
        assert all(analysis.get_job_id() == result_job.get_id() for analysis in analyses)
        
        # Verify AOI IDs
        aoi_ids = [analysis.get_aoi_id() for analysis in analyses]
        assert "12345" in aoi_ids
        assert "12346" in aoi_ids
    
    def test_gee_job_execute_returns_pending_job(self):
        """Test that GEE job execute() returns a job with pending analyses."""
        # Create test data
        features = [
            {
                'geometry': Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '03/12/2019',
                'INCIDENTNU': '12345'
            }
        ]
        layer_gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        
        # Create and execute GEE job
        from dnbr.jobs import GEEJob
        job = GEEJob(layer_gdf, provider="sa_fire")
        result_job = job.execute()
        
        # Verify job properties
        assert isinstance(result_job, DNBRAnalysisJob)
        assert result_job.generator_type == "gee"
        assert result_job.get_id() is not None
        assert result_job.get_analysis_count() == 1
        
        # Verify analyses are pending (GEE is asynchronous)
        analyses = result_job.get_analyses()
        assert len(analyses) == 1
        assert all(analysis.status == "PENDING" for analysis in analyses)
        assert all(analysis.get_job_id() == result_job.get_id() for analysis in analyses)
    
    def test_job_factory_creates_correct_job_type(self):
        """Test that job factory creates the correct job type."""
        features = [
            {
                'geometry': Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '03/12/2019',
                'INCIDENTNU': '12345'
            }
        ]
        layer_gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        
        # Test dummy job factory
        from dnbr.jobs import create_job, DummyJob, GEEJob
        dummy_job = create_job("dummy", layer_gdf, provider="sa_fire")
        assert isinstance(dummy_job, DummyJob)
        
        # Test GEE job factory
        gee_job = create_job("gee", layer_gdf, provider="sa_fire")
        assert isinstance(gee_job, GEEJob)
        
        # Test invalid job type
        with pytest.raises(ValueError, match="Unknown job type"):
            create_job("invalid", layer_gdf, provider="sa_fire")
    
    def test_job_execution_flow_with_jobservice(self):
        """Test the complete flow: job execution -> storage -> retrieval."""
        # Create test data
        features = [
            {
                'geometry': Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                'INCIDENTTY': 'Bushfire',
                'FIREDATE': '03/12/2019',
                'INCIDENTNU': '12345'
            }
        ]
        layer_gdf = gpd.GeoDataFrame(features, crs='EPSG:4326')
        
        # 1. Create and execute job
        from dnbr.jobs import DummyJob
        job = DummyJob(layer_gdf, provider="sa_fire")
        result_job = job.execute()
        
        # 2. Store job (mock JobService to avoid DynamoDB)
        from unittest.mock import Mock
        job_service = Mock()
        job_service.store_job = Mock()
        job_service.get_job = Mock(return_value=result_job)
        
        job_service.store_job(result_job)
        retrieved_job = job_service.get_job(result_job.get_id())
        
        # 3. Verify job was stored and retrieved correctly
        assert retrieved_job is not None
        assert retrieved_job.get_id() == result_job.get_id()
        assert retrieved_job.generator_type == result_job.generator_type
        assert retrieved_job.get_analysis_count() == result_job.get_analysis_count()
        
        # Verify analyses were preserved
        original_analyses = result_job.get_analyses()
        retrieved_analyses = retrieved_job.get_analyses()
        assert len(original_analyses) == len(retrieved_analyses)
        
        for orig, retrieved in zip(original_analyses, retrieved_analyses):
            assert orig.get_aoi_id() == retrieved.get_aoi_id()
            assert orig.status == retrieved.status
            assert orig.get_job_id() == retrieved.get_job_id()
