from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import datetime

class Department(str, Enum):
    """Department types"""
    ENGINEERING = "engineering"
    SALES = "sales"
    MARKETING = "marketing"
    HR = "hr"
    OPERATIONS = "operations"
    EXECUTIVE = "executive"


class Role(str, Enum):
    """User role types for access control"""
    EMPLOYEE = "employee"
    FINANCE = "finance"
    MANAGEMENT = "management"
    ADMIN = "admin"


class FileClassification(str, Enum):
    """File access classification levels"""
    PUBLIC_COMPANY = "public_company"  # All employees
    FINANCE_ONLY = "finance_only"      # Finance + Admin
    MANAGEMENT_ONLY = "management_only"  # Management + Admin
    ADMIN_ONLY = "admin_only"          # Admin only


class User(BaseModel):
    """User model for access control"""
    user_id: str
    name: str
    role: Role
    department: Optional[Department] = None
    is_active: bool = True


class FileMetadata(BaseModel):
    """Metadata for uploaded files tracking classification and access"""
    file_id: str
    filename: str
    file_type: str
    size: int
    classification: FileClassification
    uploaded_by: str
    uploaded_at: str
    is_permanent: bool = True
    expires_at: Optional[str] = None

class UploadResponse(BaseModel):
    """Response after file upload"""
    file_id: str
    filename: str
    file_type: str
    size: int
    message: str
    ai_title: Optional[str] = None

class AnalysisRequest(BaseModel):
    """Request to analyze document"""
    file_id: str
    departments: List[Department]

class DepartmentReport(BaseModel):
    """Generated report for a department"""
    department: Department
    summary: str
    key_insights: List[str]
    metrics: dict
    recommendations: Optional[List[str]] = []

class AnalysisResponse(BaseModel):
    """Response after analysis"""
    file_id: str
    filename: str
    raw_analysis: str
    reports: List[DepartmentReport]
    timestamp: str


class ChatRequest(BaseModel):
    """Request for conversational Q&A against uploaded financial data"""
    file_id: Optional[str] = None
    file_ids: Optional[List[str]] = []
    question: str
    departments: Optional[List[Department]] = []


class ChatResponse(BaseModel):
    """Response for conversational Q&A"""
    answer: str
    timestamp: str


class StudioAssetType(str, Enum):
    """Asset types generated from Studio"""
    DEPARTMENT_REPORT = "department_report"
    EXECUTIVE_BRIEF = "executive_brief"
    EMAIL_DRAFT = "email_draft"
    INFOGRAPHIC_OUTLINE = "infographic_outline"
    SLIDE_OUTLINE = "slide_outline"


class StudioRequest(BaseModel):
    """Request for studio artifact generation"""
    file_id: str
    asset_type: StudioAssetType
    department: Optional[Department] = None
    custom_prompt: Optional[str] = ""


class StudioResponse(BaseModel):
    """Response for studio artifact generation"""
    asset_type: StudioAssetType
    title: str
    content: str
    timestamp: str
