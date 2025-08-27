#!/usr/bin/env python3
"""
Tests for the AnalysisService class.
"""

import pytest
from unittest.mock import Mock, patch
from dnbr.analysis_service import AnalysisService
from dnbr.analysis import DNBRAnalysis


class TestAnalysisService:
    """Test the AnalysisService class."""
    
    def setup_method(self):
        """Set up test data."""
        # Create mock DynamoDB client
        self.mock_dynamodb = Mock()
        
        # Create analysis service with injected mock client
        self.service = AnalysisService(self.mock_dynamodb, "test-table")
        
        # Create a test analysis
        self.test_analysis = DNBRAnalysis()
        self.test_analysis._raster_urls = ["s3://test/fire_severity.tif"]
    
    def test_store_analysis(self):
        """Test storing an analysis."""
        # Act
        self.service.store_analysis(self.test_analysis)
        
        # Assert
        self.mock_dynamodb.put_item.assert_called_once()
        call_args = self.mock_dynamodb.put_item.call_args
        
        assert call_args[1]['TableName'] == "test-table"
        item = call_args[1]['Item']
        
        assert item['analysis_id']['S'] == self.test_analysis.get_id()
        assert item['status']['S'] == self.test_analysis.status
        assert len(item['raster_urls']['L']) == 1
        assert item['raster_urls']['L'][0]['S'] == "s3://test/fire_severity.tif"
        assert 'created_at' in item
        assert 'updated_at' in item
    
    def test_get_analysis_found(self):
        """Test retrieving an existing analysis."""
        # Arrange
        mock_response = {
            'Item': {
                'analysis_id': {'S': 'test-id'},
                'status': {'S': 'COMPLETED'},
                'raster_urls': {'L': [{'S': 's3://test/fire_severity.tif'}]}
            }
        }
        self.mock_dynamodb.get_item.return_value = mock_response
        
        # Act
        result = self.service.get_analysis('test-id')
        
        # Assert
        assert result is not None
        assert result.get_id() == 'test-id'
        assert result.raster_urls == ['s3://test/fire_severity.tif']
        
        self.mock_dynamodb.get_item.assert_called_once_with(
            TableName='test-table',
            Key={'analysis_id': {'S': 'test-id'}}
        )
    
    def test_get_analysis_not_found(self):
        """Test retrieving a non-existent analysis."""
        # Arrange
        self.mock_dynamodb.get_item.return_value = {}
        
        # Act
        result = self.service.get_analysis('nonexistent-id')
        
        # Assert
        assert result is None
    
    def test_list_analyses(self):
        """Test listing analyses."""
        # Arrange
        mock_response = {
            'Items': [
                {
                    'analysis_id': {'S': 'id1'},
                    'raster_urls': {'L': []}
                },
                {
                    'analysis_id': {'S': 'id2'},
                    'raster_urls': {'L': [{'S': 's3://test/file.tif'}]}
                }
            ]
        }
        self.mock_dynamodb.scan.return_value = mock_response
        
        # Act
        result = self.service.list_analyses(limit=10)
        
        # Assert
        assert len(result) == 2
        assert result[0].get_id() == 'id1'
        assert result[1].get_id() == 'id2'
        assert result[1].raster_urls == ['s3://test/file.tif']
        
        self.mock_dynamodb.scan.assert_called_once_with(
            TableName='test-table',
            Limit=10
        )
    
    def test_update_analysis_status(self):
        """Test updating analysis status."""
        # Act
        result = self.service.update_analysis_status('test-id', 'COMPLETED')
        
        # Assert
        assert result is True
        
        self.mock_dynamodb.update_item.assert_called_once()
        call_args = self.mock_dynamodb.update_item.call_args
        
        assert call_args[1]['TableName'] == 'test-table'
        assert call_args[1]['Key'] == {'analysis_id': {'S': 'test-id'}}
        assert call_args[1]['UpdateExpression'] == 'SET #status = :status, updated_at = :updated_at'
        assert call_args[1]['ExpressionAttributeNames'] == {'#status': 'status'}
        assert ':status' in call_args[1]['ExpressionAttributeValues']
        assert ':updated_at' in call_args[1]['ExpressionAttributeValues'] 