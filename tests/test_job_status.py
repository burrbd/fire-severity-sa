#!/usr/bin/env python3
"""
Tests for job status methods focusing on behavior.
Tests job completion, failure, and status transitions.
"""

import pytest
from dnbr.job import DNBRAnalysisJob
from dnbr.analysis import DNBRAnalysis


class TestJobStatus:
    """Test job status behavior and transitions."""
    
    def test_job_with_all_completed_analyses_is_complete(self):
        """Test that job is complete when all analyses are completed."""
        job = DNBRAnalysisJob(generator_type="dummy")
        
        # Add completed analyses
        analysis1 = DNBRAnalysis(generator_type="dummy", job_id=job.get_id())
        analysis1.set_status("COMPLETED")
        job.add_analysis(analysis1)
        
        analysis2 = DNBRAnalysis(generator_type="dummy", job_id=job.get_id())
        analysis2.set_status("COMPLETED")
        job.add_analysis(analysis2)
        
        # Verify job is complete
        assert job.is_complete() is True
        assert job.is_failed() is False
        assert len(job.get_completed_analyses()) == 2
        assert len(job.get_pending_analyses()) == 0
        assert len(job.get_failed_analyses()) == 0
    
    def test_job_with_pending_analyses_is_not_complete(self):
        """Test that job is not complete when analyses are pending."""
        job = DNBRAnalysisJob(generator_type="gee")
        
        # Add pending analyses
        analysis1 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis1.set_status("PENDING")
        job.add_analysis(analysis1)
        
        analysis2 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis2.set_status("PENDING")
        job.add_analysis(analysis2)
        
        # Verify job is not complete
        assert job.is_complete() is False
        assert job.is_failed() is False
        assert len(job.get_completed_analyses()) == 0
        assert len(job.get_pending_analyses()) == 2
        assert len(job.get_failed_analyses()) == 0
    
    def test_job_with_failed_analyses_is_failed(self):
        """Test that job is failed when any analysis has failed."""
        job = DNBRAnalysisJob(generator_type="gee")
        
        # Add mixed status analyses
        analysis1 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis1.set_status("COMPLETED")
        job.add_analysis(analysis1)
        
        analysis2 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis2.set_status("FAILED")
        job.add_analysis(analysis2)
        
        # Verify job is failed
        assert job.is_complete() is False
        assert job.is_failed() is True
        assert len(job.get_completed_analyses()) == 1
        assert len(job.get_pending_analyses()) == 0
        assert len(job.get_failed_analyses()) == 1
    
    def test_job_with_mixed_status_analyses(self):
        """Test job with mixed status analyses."""
        job = DNBRAnalysisJob(generator_type="gee")
        
        # Add analyses with different statuses
        analysis1 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis1.set_status("COMPLETED")
        job.add_analysis(analysis1)
        
        analysis2 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis2.set_status("PENDING")
        job.add_analysis(analysis2)
        
        analysis3 = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis3.set_status("FAILED")
        job.add_analysis(analysis3)
        
        # Verify counts
        assert job.get_analysis_count() == 3
        assert len(job.get_completed_analyses()) == 1
        assert len(job.get_pending_analyses()) == 1
        assert len(job.get_failed_analyses()) == 1
        
        # Verify overall status
        assert job.is_complete() is False
        assert job.is_failed() is True
    
    def test_empty_job_status(self):
        """Test status of empty job."""
        job = DNBRAnalysisJob(generator_type="dummy")
        
        # Verify empty job status
        assert job.get_analysis_count() == 0
        assert len(job.get_completed_analyses()) == 0
        assert len(job.get_pending_analyses()) == 0
        assert len(job.get_failed_analyses()) == 0
        assert job.is_complete() is True  # Empty job is technically complete
        assert job.is_failed() is False
    
    def test_job_status_transitions(self):
        """Test job status transitions as analyses change status."""
        job = DNBRAnalysisJob(generator_type="gee")
        
        # Start with pending analysis
        analysis = DNBRAnalysis(generator_type="gee", job_id=job.get_id())
        analysis.set_status("PENDING")
        job.add_analysis(analysis)
        
        # Initially pending
        assert job.is_complete() is False
        assert job.is_failed() is False
        assert len(job.get_pending_analyses()) == 1
        
        # Transition to completed
        analysis.set_status("COMPLETED")
        assert job.is_complete() is True
        assert job.is_failed() is False
        assert len(job.get_completed_analyses()) == 1
        assert len(job.get_pending_analyses()) == 0
        
        # Transition to failed
        analysis.set_status("FAILED")
        assert job.is_complete() is False
        assert job.is_failed() is True
        assert len(job.get_failed_analyses()) == 1
        assert len(job.get_completed_analyses()) == 0
    
    def test_job_to_json_representation(self):
        """Test that job can be converted to JSON representation."""
        job = DNBRAnalysisJob(generator_type="dummy")
        
        # Add analyses with different statuses
        analysis1 = DNBRAnalysis(generator_type="dummy", job_id=job.get_id())
        analysis1.set_status("COMPLETED")
        job.add_analysis(analysis1)
        
        analysis2 = DNBRAnalysis(generator_type="dummy", job_id=job.get_id())
        analysis2.set_status("PENDING")
        job.add_analysis(analysis2)
        
        # Convert to JSON
        job_json = job.to_json()
        
        # Verify JSON structure
        assert job_json["job_id"] == job.get_id()
        assert job_json["generator_type"] == "dummy"
        assert job_json["created_at"] == job.get_created_at()
        assert job_json["analysis_count"] == 2
        assert job_json["completed_count"] == 1
        assert job_json["pending_count"] == 1
        assert job_json["failed_count"] == 0
        assert job_json["is_complete"] is False
        assert job_json["is_failed"] is False
        assert len(job_json["analyses"]) == 2
        
        # Verify analyses in JSON (they are JSON strings, need to parse)
        import json
        analyses_json = [json.loads(analysis) for analysis in job_json["analyses"]]
        assert analyses_json[0]["status"] == "COMPLETED"
        assert analyses_json[1]["status"] == "PENDING"
