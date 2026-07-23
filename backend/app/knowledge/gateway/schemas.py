"""
Phase 14.1 Enterprise Knowledge Gateway — Pydantic Schemas.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class IngestAssetRequest(BaseModel):
    title: str = Field(..., description="Human readable title or subject of asset")
    content_or_uri: str = Field(..., description="Raw text content or S3/HTTP URL of asset")
    asset_type: str = Field("pdf", description="crm | voice | meetings | emails | pdf | word | excel | powerpoint | csv | json | markdown | images | web_url | research | manual_notes | lead_discovery | company_intelligence | workflow_outputs | ai_reports | webhook_events | raw_text")
    user_id: str = Field("user_default", description="User owner identifier")
    org_id: Optional[str] = Field(None, description="Organization ID for multi-tenant isolation")
    security_acl: Optional[List[str]] = Field(None, description="ACL role permissions list")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata tags")
    job_id: Optional[str] = Field(None, description="Import job ID if part of bulk import")


class KnowledgeObjectResponse(BaseModel):
    document_id: str
    user_id: str
    org_id: Optional[str] = None
    title: str
    file_type: str
    file_size_bytes: int
    source_uri: Optional[str] = None
    security_acl: List[str]
    is_validated: bool
    virus_scan_passed: bool
    status: str
    version: int
    total_chunks: int
    language: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class CreateImportJobRequest(BaseModel):
    source_name: str = Field(..., description="Source system name e.g. Salesforce_CRM")
    file_count: int = Field(1, ge=1, description="Total expected files in job")
    user_id: str = Field("user_default")


class ImportJobResponse(BaseModel):
    job_id: str
    user_id: str
    source_name: str
    file_count: int
    status: str
    processed_count: int
    error_log: Optional[str] = None
    created_at: datetime


class CreateSourceRequest(BaseModel):
    name: str = Field(..., description="Display name of source connector")
    source_type: str = Field("crm", description="crm | voice | meetings | emails | webhooks | s3 | manual")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SourceConfigResponse(BaseModel):
    source_id: str
    name: str
    source_type: str
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime


class ValidationResultResponse(BaseModel):
    validation_id: str
    document_id: str
    quota_passed: bool
    virus_scan_passed: bool
    acl_passed: bool
    details: Dict[str, Any]
    created_at: datetime
