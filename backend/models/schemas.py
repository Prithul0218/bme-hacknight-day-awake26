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


class SourceChunk(BaseModel):
    """Information about a source chunk used in a response"""
    file_id: str
    filename: str
    chunk_id: int
    start_char: int
    end_char: int
    text_preview: str  # First 200 chars of the chunk
    relevance_score: float


class Citation(BaseModel):
    """Citation linking response to source document"""
    citation_id: int  # [1], [2], etc.
    file_id: str
    filename: str
    chunk_id: int
    start_char: int
    end_char: int
    relevance_score: float
    text_preview: str  # Short preview of cited text


class ChatResponse(BaseModel):
    """Response for conversational Q&A"""
    answer: str
    timestamp: str
    citations: List[Citation] = []


class StudioAssetType(str, Enum):
    """Asset types generated from Studio"""
    DEPARTMENT_REPORT = "department_report"
    EXECUTIVE_BRIEF = "executive_brief"
    EMAIL_DRAFT = "email_draft"
    INFOGRAPHIC_OUTLINE = "infographic_outline"
    SLIDE_OUTLINE = "slide_outline"


class StudioComplexity(str, Enum):
    """Complexity level requested for studio assets"""
    BRIEF = "brief"
    STANDARD = "standard"
    DETAILED = "detailed"


class StudioLength(str, Enum):
    """Length target requested for studio assets"""
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class StudioRequest(BaseModel):
    """Request for studio artifact generation"""
    file_id: str
    asset_type: StudioAssetType
    department: Optional[Department] = None
    custom_prompt: Optional[str] = ""
    complexity: StudioComplexity = StudioComplexity.STANDARD
    length: StudioLength = StudioLength.MEDIUM


class StudioResponse(BaseModel):
    """Response for studio artifact generation"""
    asset_type: StudioAssetType
    title: str
    content: str
    timestamp: str
    image_data_url: Optional[str] = None
    citations: List[Citation] = []


class AlertMetric(str, Enum):
    """Metrics supported by quick alerts"""
    REVENUE = "revenue"
    OPERATING_EXPENSE = "operating_expense"
    DEPARTMENT_SPEND = "department_spend"
    CASH_BALANCE = "cash_balance"
    BURN_RATE = "burn_rate"
    AR_AGING = "ar_aging"
    AP_AGING = "ap_aging"
    BUDGET_VARIANCE_PERCENT = "budget_variance_percent"


class AlertCondition(str, Enum):
    """Condition operators for quick alerts"""
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN_OR_EQUAL = "<="
    CHANGES_BY_PERCENT = "changes_by_percent"


class AlertTimeWindow(str, Enum):
    """Evaluation windows for quick alerts"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class AlertDigestMode(str, Enum):
    """Alert delivery cadence"""
    REALTIME = "realtime"
    DAILY_DIGEST = "daily_digest"
    WEEKLY_DIGEST = "weekly_digest"


class AlertChannel(str, Enum):
    """Delivery channels for alerts"""
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"


class AlertStatus(str, Enum):
    """Alert activation status"""
    ACTIVE = "active"
    PAUSED = "paused"


class QuickAlertCreateRequest(BaseModel):
    """Request for creating a quick dropdown alert"""
    alert_name: str
    metric: AlertMetric
    condition: AlertCondition
    threshold_value: float
    time_window: AlertTimeWindow
    scope_department: Optional[Department] = None
    severity: AlertSeverity = AlertSeverity.MEDIUM
    delivery_channels: List[AlertChannel] = [AlertChannel.IN_APP]
    digest_mode: AlertDigestMode = AlertDigestMode.REALTIME


class AlertUpdateRequest(BaseModel):
    """Request for updating alert status"""
    status: AlertStatus


class AlertResponse(BaseModel):
    """Alert payload returned to client"""
    alert_id: str
    alert_name: str
    metric: AlertMetric
    condition: AlertCondition
    threshold_value: float
    time_window: AlertTimeWindow
    scope_department: Optional[Department] = None
    severity: AlertSeverity
    delivery_channels: List[AlertChannel]
    digest_mode: AlertDigestMode
    status: AlertStatus
    created_by: str
    created_at: str
    last_triggered_at: Optional[str] = None
