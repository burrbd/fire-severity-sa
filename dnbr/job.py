#!/usr/bin/env python3
"""
Job management for batch dNBR analysis processing.
"""

from typing import List, Dict, Any
from datetime import datetime
import ulid
from .analysis import DNBRAnalysis


class DNBRAnalysisJob:
    """Represents a batch job containing multiple dNBR analyses."""
    
    def __init__(self, generator_type: str = "unknown"):
        """
        Initialize a dNBR analysis job.
        
        Args:
            generator_type: Type of generator used ("dummy", "gee", etc.)
        """
        self._id = str(ulid.ULID())
        self._generator_type = generator_type
        self._created_at = datetime.utcnow().isoformat()
        self._analyses: List[DNBRAnalysis] = []
    
    def get_id(self) -> str:
        """Get the unique job ID."""
        return self._id
    
    @property
    def generator_type(self) -> str:
        """Get the generator type used for this job."""
        return self._generator_type
    
    def get_created_at(self) -> str:
        """Get the creation timestamp."""
        return self._created_at
    
    def add_analysis(self, analysis: DNBRAnalysis) -> None:
        """Add an analysis to this job."""
        analysis._job_id = self._id
        self._analyses.append(analysis)
    
    def get_analyses(self) -> List[DNBRAnalysis]:
        """Get all analyses in this job."""
        return self._analyses
    
    def get_analysis_count(self) -> int:
        """Get the number of analyses in this job."""
        return len(self._analyses)
    
    def get_completed_analyses(self) -> List[DNBRAnalysis]:
        """Get all completed analyses in this job."""
        return [analysis for analysis in self._analyses if analysis.status == "COMPLETED"]
    
    def get_pending_analyses(self) -> List[DNBRAnalysis]:
        """Get all pending analyses in this job."""
        return [analysis for analysis in self._analyses if analysis.status == "PENDING"]
    
    def get_failed_analyses(self) -> List[DNBRAnalysis]:
        """Get all failed analyses in this job."""
        return [analysis for analysis in self._analyses if analysis.status == "FAILED"]
    
    def is_complete(self) -> bool:
        """Check if all analyses in the job are completed."""
        return all(analysis.status == "COMPLETED" for analysis in self._analyses)
    
    def is_failed(self) -> bool:
        """Check if any analyses in the job have failed."""
        return any(analysis.status == "FAILED" for analysis in self._analyses)
    
    def to_json(self) -> Dict[str, Any]:
        """Convert job to JSON representation."""
        return {
            "job_id": self._id,
            "generator_type": self._generator_type,
            "created_at": self._created_at,
            "analysis_count": len(self._analyses),
            "completed_count": len(self.get_completed_analyses()),
            "pending_count": len(self.get_pending_analyses()),
            "failed_count": len(self.get_failed_analyses()),
            "is_complete": self.is_complete(),
            "is_failed": self.is_failed(),
            "analyses": [analysis.to_json() for analysis in self._analyses]
        }
