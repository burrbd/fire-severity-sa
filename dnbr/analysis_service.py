#!/usr/bin/env python3
"""
Analysis service for managing analysis metadata and database operations.
This is the single point of database access for all analysis operations.
"""

from typing import Optional, List
import json
import os
from datetime import datetime
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from .analysis import DNBRAnalysis


def create_analysis_service(table_name: str = None, region: str = None):
    """
    Factory function to create AnalysisService with proper configuration.
    
    Args:
        table_name: DynamoDB table name (defaults to environment variable)
        region: AWS region (defaults to environment variable)
        
    Returns:
        AnalysisService instance with configured DynamoDB client
        
    Raises:
        ValueError: If AWS credentials are not available
        ClientError: If DynamoDB table does not exist
    """
    # Get configuration from environment variables or use defaults
    table_name = table_name or os.getenv('AWS_DYNAMODB_TABLE_NAME', 'fire-severity-analyses-dev')
    region = region or os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    try:
        # Create DynamoDB client
        dynamodb = boto3.client('dynamodb', region_name=region)
        
        # Test the connection
        dynamodb.describe_table(TableName=table_name)
        
        return AnalysisService(dynamodb, table_name)
        
    except NoCredentialsError:
        raise ValueError("AWS credentials not found. Please configure AWS credentials.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            raise ValueError(f"DynamoDB table '{table_name}' not found. Create it using the CloudFormation template.")
        else:
            raise


class AnalysisService:
    """Service for storing and retrieving analysis metadata from DynamoDB."""
    
    def __init__(self, dynamodb_client, table_name: str):
        """
        Initialize the analysis service.
        
        Args:
            dynamodb_client: Boto3 DynamoDB client instance
            table_name: DynamoDB table name for storing analyses
        """
        self.dynamodb = dynamodb_client
        self.table_name = table_name
    
    def store_analysis(self, analysis: DNBRAnalysis) -> None:
        """
        Store analysis metadata in DynamoDB.
        
        Args:
            analysis: Analysis object to store
        """
        # Prepare item for DynamoDB
        item = {
            'analysis_id': {'S': analysis.get_id()},
            'status': {'S': analysis.status},
            'generator_type': {'S': analysis.generator_type},
            'raster_urls': {'L': [{'S': url} for url in analysis.raster_urls]},
            'created_at': {'S': datetime.utcnow().isoformat()},
            'updated_at': {'S': datetime.utcnow().isoformat()}
        }
        
        # Store in DynamoDB
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item
        )

    
    def get_analysis(self, analysis_id: str) -> Optional[DNBRAnalysis]:
        """
        Retrieve analysis metadata from DynamoDB.
        
        Args:
            analysis_id: Analysis ID to retrieve
            
        Returns:
            Analysis object if found, None otherwise
        """
        response = self.dynamodb.get_item(
            TableName=self.table_name,
            Key={'analysis_id': {'S': analysis_id}}
        )
        
        if 'Item' not in response:
            return None
        
        item = response['Item']
        
        # Create a concrete analysis object
        analysis = DNBRAnalysis()
        analysis._id = item['analysis_id']['S']
        
        # Extract raster URLs
        if 'raster_urls' in item:
            analysis._raster_urls = [url['S'] for url in item['raster_urls']['L']]
        
        return analysis
    
    def list_analyses(self, limit: int = 100) -> List[DNBRAnalysis]:
        """
        List all analyses in the database.
        
        Args:
            limit: Maximum number of analyses to return
            
        Returns:
            List of analysis objects
        """
        response = self.dynamodb.scan(
            TableName=self.table_name,
            Limit=limit
        )
        
        analyses = []
        for item in response.get('Items', []):
            analysis = DNBRAnalysis()
            analysis._id = item['analysis_id']['S']
            
            if 'raster_urls' in item:
                analysis._raster_urls = [url['S'] for url in item['raster_urls']['L']]
            
            analyses.append(analysis)
        
        return analyses
    
    def update_analysis_status(self, analysis_id: str, status: str) -> bool:
        """
        Update the status of an analysis.
        
        Args:
            analysis_id: Analysis ID to update
            status: New status value
            
        Returns:
            True if update was successful, False otherwise
        """
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key={'analysis_id': {'S': analysis_id}},
            UpdateExpression='SET #status = :status, updated_at = :updated_at',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': {'S': status},
                ':updated_at': {'S': datetime.utcnow().isoformat()}
            }
        )
        return True 