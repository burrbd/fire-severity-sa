#!/usr/bin/env python3
"""
Integration tests for JobService focusing on behavior.
Tests the complete job lifecycle: create, store, retrieve, update.
"""

import pytest
import geopandas as gpd
from shapely.geometry import Polygon
from unittest.mock import patch, MagicMock
from dnbr.job_service import create_job_service, JobService
from dnbr.jobs import DummyJob, GEEJob
from dnbr.job import DNBRAnalysisJob


class TestJobServiceIntegration:
    """Test JobService integration with real job objects."""
    
    def test_job_service_stores_and_retrieves_dummy_job(self):
        """Test that JobService can store and retrieve a dummy job."""
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
        
        # Create and execute job
        job = DummyJob(layer_gdf, provider="sa_fire")
        result_job = job.execute()
        
        # Mock JobService to avoid DynamoDB
        with patch('dnbr.job_service.boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            
            # Mock successful table description
            mock_dynamodb.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
            
            # Create service
            service = create_job_service()
            
            # Store job
            service.store_job(result_job)
            
            # Verify store_job was called with correct data
            mock_dynamodb.put_item.assert_called_once()
            call_args = mock_dynamodb.put_item.call_args
            item = call_args[1]['Item']
            
            # Verify job data was stored correctly
            assert item['job_id']['S'] == result_job.get_id()
            assert item['generator_type']['S'] == 'dummy'
            assert item['analysis_count']['N'] == '1'
            
            # Mock retrieval
            mock_dynamodb.get_item.return_value = {
                'Item': item
            }
            
            # Retrieve job
            retrieved_job = service.get_job(result_job.get_id())
            
            # Verify job was retrieved correctly
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
    
    def test_job_service_stores_and_retrieves_gee_job(self):
        """Test that JobService can store and retrieve a GEE job with pending analyses."""
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
        
        # Create and execute job
        job = GEEJob(layer_gdf, provider="sa_fire")
        result_job = job.execute()
        
        # Mock JobService
        with patch('dnbr.job_service.boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            mock_dynamodb.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
            
            service = create_job_service()
            service.store_job(result_job)
            
            # Verify GEE job was stored with pending analyses
            call_args = mock_dynamodb.put_item.call_args
            item = call_args[1]['Item']
            
            assert item['job_id']['S'] == result_job.get_id()
            assert item['generator_type']['S'] == 'gee'
            assert item['analysis_count']['N'] == '1'
            
            # Mock retrieval
            mock_dynamodb.get_item.return_value = {'Item': item}
            
            # Retrieve job
            retrieved_job = service.get_job(result_job.get_id())
            
            # Verify GEE job has pending analyses
            assert retrieved_job is not None
            assert retrieved_job.generator_type == 'gee'
            analyses = retrieved_job.get_analyses()
            assert len(analyses) == 1
            assert all(analysis.status == 'PENDING' for analysis in analyses)
    
    def test_job_service_handles_missing_job(self):
        """Test that JobService returns None for non-existent jobs."""
        with patch('dnbr.job_service.boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            mock_dynamodb.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
            
            service = create_job_service()
            
            # Mock empty response
            mock_dynamodb.get_item.return_value = {}
            
            # Try to retrieve non-existent job
            result = service.get_job('non-existent-job-id')
            
            # Should return None
            assert result is None
    
    def test_job_service_updates_job_status(self):
        """Test that JobService can update job status."""
        with patch('dnbr.job_service.boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            mock_dynamodb.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
            
            service = create_job_service()
            
            # Update job status
            service.update_job_status('test-job-id', 'COMPLETED')
            
            # Verify update was called
            mock_dynamodb.update_item.assert_called_once()
            call_args = mock_dynamodb.update_item.call_args
            
            # Verify correct job ID and update expression
            assert call_args[1]['Key']['job_id']['S'] == 'test-job-id'
            assert call_args[1]['ExpressionAttributeValues'][':updated_at']['S'] is not None
    
    def test_job_service_lists_jobs(self):
        """Test that JobService can list jobs."""
        with patch('dnbr.job_service.boto3.client') as mock_boto3:
            mock_dynamodb = MagicMock()
            mock_boto3.return_value = mock_dynamodb
            mock_dynamodb.describe_table.return_value = {'Table': {'TableStatus': 'ACTIVE'}}
            
            # Mock scan response with job data
            mock_dynamodb.scan.return_value = {
                'Items': [
                    {
                        'job_id': {'S': 'job-1'},
                        'generator_type': {'S': 'dummy'},
                        'created_at': {'S': '2025-08-29T00:00:00'},
                        'analysis_count': {'N': '1'},
                        'analyses': {'S': '[{"aoi_id": "12345", "status": "COMPLETED"}]'}
                    },
                    {
                        'job_id': {'S': 'job-2'},
                        'generator_type': {'S': 'gee'},
                        'created_at': {'S': '2025-08-29T01:00:00'},
                        'analysis_count': {'N': '2'},
                        'analyses': {'S': '[{"aoi_id": "12346", "status": "PENDING"}]'}
                    }
                ]
            }
            
            service = create_job_service()
            jobs = service.list_jobs()
            
            # Verify jobs were retrieved
            assert len(jobs) == 2
            assert jobs[0].get_id() == 'job-1'
            assert jobs[0].generator_type == 'dummy'
            assert jobs[1].get_id() == 'job-2'
            assert jobs[1].generator_type == 'gee'
            
            # Verify scan was called with correct parameters
            mock_dynamodb.scan.assert_called_once_with(
                TableName='fire-severity-jobs-dev',
                Limit=100
            )
