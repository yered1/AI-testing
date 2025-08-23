# orchestrator/models/finding.py
"""
SQLAlchemy model for findings table
"""
from sqlalchemy import Column, String, Text, Float, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Finding(Base):
    """Finding model for vulnerability tracking"""
    __tablename__ = 'findings'
    
    # Primary fields
    id = Column(String, primary_key=True)
    tenant_id = Column(String, nullable=False, index=True)
    run_id = Column(String, ForeignKey('runs.id'), nullable=False, index=True)
    engagement_id = Column(String, ForeignKey('engagements.id'), nullable=False, index=True)
    job_id = Column(String, ForeignKey('jobs.id'), nullable=True)
    agent_id = Column(String, ForeignKey('agents.id'), nullable=True)
    
    # Finding details
    title = Column(String, nullable=False)
    severity = Column(String, nullable=False, index=True)  # critical, high, medium, low, info
    category = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=False)
    
    # Evidence and affected resources
    evidence = Column(JSONB, nullable=True)
    affected_hosts = Column(ARRAY(String), nullable=True)
    affected_urls = Column(ARRAY(String), nullable=True)
    
    # Vulnerability identifiers
    cve_ids = Column(ARRAY(String), nullable=True)
    cwe_ids = Column(ARRAY(String), nullable=True)
    owasp_category = Column(String, nullable=True)
    cvss_vector = Column(String, nullable=True)
    cvss_score = Column(Float, nullable=True)
    
    # Remediation
    remediation = Column(Text, nullable=True)
    references = Column(ARRAY(String), nullable=True)
    
    # Status tracking
    false_positive = Column(Boolean, default=False, nullable=False)
    duplicate_of = Column(String, ForeignKey('findings.id'), nullable=True)
    status = Column(String, default='open', nullable=False, index=True)  # open, in_progress, resolved, accepted, false_positive
    hash = Column(String, nullable=False, index=True)  # For deduplication
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    run = relationship("Run", back_populates="findings")
    engagement = relationship("Engagement", back_populates="findings")
    job = relationship("Job", back_populates="findings")
    agent = relationship("Agent", back_populates="findings")
    duplicate_findings = relationship("Finding", backref="original_finding", remote_side=[id])
    comments = relationship("FindingComment", back_populates="finding", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convert finding to dictionary"""
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'run_id': self.run_id,
            'engagement_id': self.engagement_id,
            'job_id': self.job_id,
            'agent_id': self.agent_id,
            'title': self.title,
            'severity': self.severity,
            'category': self.category,
            'description': self.description,
            'evidence': self.evidence,
            'affected_hosts': self.affected_hosts,
            'affected_urls': self.affected_urls,
            'cve_ids': self.cve_ids,
            'cwe_ids': self.cwe_ids,
            'owasp_category': self.owasp_category,
            'cvss_vector': self.cvss_vector,
            'cvss_score': self.cvss_score,
            'remediation': self.remediation,
            'references': self.references,
            'false_positive': self.false_positive,
            'duplicate_of': self.duplicate_of,
            'status': self.status,
            'hash': self.hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_risk_score(self):
        """Calculate risk score based on severity and CVSS"""
        severity_scores = {
            'critical': 10,
            'high': 8,
            'medium': 5,
            'low': 2,
            'info': 1
        }
        
        base_score = severity_scores.get(self.severity.lower(), 5)
        
        # Adjust based on CVSS if available
        if self.cvss_score:
            return (base_score + self.cvss_score) / 2
        
        return base_score


class FindingComment(Base):
    """Comments on findings for collaboration"""
    __tablename__ = 'finding_comments'
    
    id = Column(String, primary_key=True)
    finding_id = Column(String, ForeignKey('findings.id'), nullable=False, index=True)
    tenant_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    finding = relationship("Finding", back_populates="comments")
    
    def to_dict(self):
        return {
            'id': self.id,
            'finding_id': self.finding_id,
            'user_id': self.user_id,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }