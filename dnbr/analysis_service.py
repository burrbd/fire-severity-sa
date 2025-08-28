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
    region = region or os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2')
    
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
        # Convert analysis to DynamoDB format
        item = self._to_dynamodb_item(analysis)
        
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
        
        # Convert DynamoDB item to analysis object
        return self._from_dynamodb_item(response['Item'])
    
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
        
        # Convert DynamoDB items to analysis objects
        return [self._from_dynamodb_item(item) for item in response.get('Items', [])]
    
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
    
    def _to_dynamodb_item(self, analysis: DNBRAnalysis) -> dict:
        """
        Convert analysis object to DynamoDB item format.
        
        Args:
            analysis: Analysis object
            
        Returns:
            DynamoDB item dictionary
        """
        import json
        from datetime import datetime
        
        # Get JSON data from analysis
        json_data = json.loads(analysis.to_json())
        
        item = {
            'analysis_id': {'S': analysis.get_id()},
            'status': {'S': analysis.status},
            'generator_type': {'S': analysis.generator_type},
            'raw_raster_path': {'S': analysis.raw_raster_path or ''},
            'published_dnbr_raster_url': {'S': analysis.published_dnbr_raster_url or ''},
            'published_vector_url': {'S': analysis.published_vector_url or ''},
            'created_at': {'S': analysis.get_created_at()},
            'updated_at': {'S': datetime.utcnow().isoformat()}
        }
        
        # Add fire metadata if present
        if analysis.fire_metadata:
            item['fire_metadata'] = {'S': json.dumps(analysis.fire_metadata.to_dict())}
        
        return item
    
    def _from_dynamodb_item(self, item: dict) -> DNBRAnalysis:
        """
        Convert DynamoDB item format to analysis object.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            Analysis object
        """
        import json
        
        # Build JSON data for analysis reconstruction
        json_data = {
            'id': item['analysis_id']['S'],
            'status': item.get('status', {}).get('S', 'PENDING'),
            'generator_type': item.get('generator_type', {}).get('S', 'unknown'),
            'raw_raster_path': item.get('raw_raster_path', {}).get('S'),
            'published_dnbr_raster_url': item.get('published_dnbr_raster_url', {}).get('S'),
            'published_vector_url': item.get('published_vector_url', {}).get('S'),
            'created_at': item.get('created_at', {}).get('S', '')
        }
        
        # Add fire metadata if present
        if 'fire_metadata' in item:
            json_data['fire_metadata'] = json.loads(item['fire_metadata']['S'])
        
        # Use existing from_json method
        return DNBRAnalysis.from_json(json.dumps(json_data)) 