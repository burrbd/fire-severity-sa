#!/usr/bin/env python3
"""
Service for storing and retrieving dNBR analysis jobs from DynamoDB.
"""

import boto3
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from botocore.exceptions import ClientError, NoCredentialsError
from .job import DNBRAnalysisJob
from .analysis import DNBRAnalysis


def create_job_service(dynamodb_client=None, table_name: str = None) -> 'JobService':
    """
    Create a job service for storing analysis jobs.
    
    Args:
        dynamodb_client: Optional DynamoDB client instance
        table_name: Optional table name override
        
    Returns:
        JobService instance
        
    Raises:
        RuntimeError: If credentials or table not available
    """
    try:
        # Use provided client or create new one
        if dynamodb_client is None:
            dynamodb_client = boto3.client('dynamodb', region_name='ap-southeast-2')
        
        # Use provided table name or default
        if table_name is None:
            table_name = 'fire-severity-jobs-dev'
        
        # Verify table exists
        try:
            dynamodb_client.describe_table(TableName=table_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise RuntimeError(f"DynamoDB table '{table_name}' not found")
            else:
                raise RuntimeError(f"Failed to access DynamoDB table: {e}")
        
        return JobService(dynamodb_client, table_name)
        
    except NoCredentialsError:
        raise RuntimeError("AWS credentials not found")
    except Exception as e:
        raise RuntimeError(f"Failed to create job service: {e}")


class JobService:
    """Service for storing and retrieving analysis jobs from DynamoDB."""
    
    def __init__(self, dynamodb_client, table_name: str):
        """
        Initialize the job service.
        
        Args:
            dynamodb_client: Boto3 DynamoDB client instance
            table_name: DynamoDB table name for storing jobs
        """
        self.dynamodb = dynamodb_client
        self.table_name = table_name
    
    def store_job(self, job: DNBRAnalysisJob) -> None:
        """
        Store job in DynamoDB.
        
        Args:
            job: Job object to store
        """
        # Convert job to DynamoDB format
        item = self._to_dynamodb_item(job)
        
        # Store in DynamoDB
        self.dynamodb.put_item(
            TableName=self.table_name,
            Item=item
        )
    
    def get_job(self, job_id: str) -> Optional[DNBRAnalysisJob]:
        """
        Retrieve job from DynamoDB.
        
        Args:
            job_id: Job ID to retrieve
            
        Returns:
            Job object if found, None otherwise
        """
        response = self.dynamodb.get_item(
            TableName=self.table_name,
            Key={'job_id': {'S': job_id}}
        )
        
        if 'Item' not in response:
            return None
        
        # Convert DynamoDB item to job object
        return self._from_dynamodb_item(response['Item'])
    
    def list_jobs(self, limit: int = 100) -> List[DNBRAnalysisJob]:
        """
        List all jobs in the database.
        
        Args:
            limit: Maximum number of jobs to return
            
        Returns:
            List of job objects
        """
        response = self.dynamodb.scan(
            TableName=self.table_name,
            Limit=limit
        )
        
        # Convert DynamoDB items to job objects
        return [self._from_dynamodb_item(item) for item in response.get('Items', [])]
    
    def update_job_status(self, job_id: str, status: str) -> bool:
        """
        Update the status of a job.
        
        Args:
            job_id: Job ID to update
            status: New status value (not used in current implementation)
            
        Returns:
            True if update was successful, False otherwise
        """
        # Note: Individual analysis statuses are stored within the job
        # This method could be enhanced to update specific analysis statuses
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key={'job_id': {'S': job_id}},
            UpdateExpression='SET updated_at = :updated_at',
            ExpressionAttributeValues={
                ':updated_at': {'S': datetime.utcnow().isoformat()}
            }
        )
        return True
    
    def _to_dynamodb_item(self, job: DNBRAnalysisJob) -> dict:
        """
        Convert job object to DynamoDB item format.
        
        Args:
            job: Job object
            
        Returns:
            DynamoDB item dictionary
        """
        # Convert analyses to simplified format (no ULIDs needed)
        analyses_data = []
        for analysis in job.get_analyses():
            analysis_data = {
                'aoi_id': analysis.get_aoi_id(),
                'status': analysis.status,
                'raw_raster_url': analysis.raw_raster_url or '',
                'source_vector_url': analysis.source_vector_url or '',
                'published_dnbr_raster_url': analysis.published_dnbr_raster_url or '',
                'published_vector_url': analysis.published_vector_url or '',
                'fire_date': analysis.get_fire_date() or '',
                'provider': analysis.get_provider() or ''
            }
            analyses_data.append(analysis_data)
        
        item = {
            'job_id': {'S': job.get_id()},
            'generator_type': {'S': job.generator_type},
            'created_at': {'S': job.get_created_at()},
            'updated_at': {'S': datetime.utcnow().isoformat()},
            'analysis_count': {'N': str(len(job.get_analyses()))},
            'analyses': {'S': json.dumps(analyses_data)}
        }
        
        return item
    
    def _from_dynamodb_item(self, item: dict) -> DNBRAnalysisJob:
        """
        Convert DynamoDB item format to job object.
        
        Args:
            item: DynamoDB item dictionary
            
        Returns:
            Job object
        """
        # Create job
        job = DNBRAnalysisJob(generator_type=item.get('generator_type', {}).get('S', 'unknown'))
        
        # Override the generated ID with the stored one
        job._id = item['job_id']['S']
        job._created_at = item.get('created_at', {}).get('S', job._created_at)
        
        # Reconstruct analyses from stored data
        analyses_data = json.loads(item.get('analyses', {}).get('S', '[]'))
        for analysis_data in analyses_data:
            # Create analysis without ULID (just for reconstruction)
            analysis = DNBRAnalysis(
                generator_type=job.generator_type,
                job_id=job._id
            )
            
            # Set properties from stored data
            analysis._status = analysis_data.get('status', 'PENDING')
            analysis._raw_raster_url = analysis_data.get('raw_raster_url')
            analysis._source_vector_url = analysis_data.get('source_vector_url')
            analysis._published_dnbr_raster_url = analysis_data.get('published_dnbr_raster_url')
            analysis._published_vector_url = analysis_data.get('published_vector_url')
            
            # Reconstruct fire metadata if available
            if analysis_data.get('fire_date') and analysis_data.get('provider'):
                from .fire_metadata import SAFireMetadata
                fire_metadata = SAFireMetadata(
                    "Bushfire",  # Default type
                    analysis_data['fire_date'],
                    {"INCIDENTNU": analysis_data['aoi_id']}  # Use aoi_id as incident number
                )
                analysis._fire_metadata = fire_metadata
            
            # Add to job
            job._analyses.append(analysis)
        
        return job
