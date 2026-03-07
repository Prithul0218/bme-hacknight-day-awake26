from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from pydantic import BaseModel
from backend.models.schemas import (
    UploadResponse,
    AnalysisRequest,
    AnalysisResponse,
    ChatRequest,
    ChatResponse,
    StudioRequest,
    StudioResponse,
    FileClassification,
    FileMetadata,
)
from backend.services.document_processor import DocumentProcessor
from backend.services.gemini_service import GeminiService
from backend.services.report_generator import ReportGenerator
from backend.services.rag_service import rag_service
from backend.services.access_control import (
    can_user_access_file,
    get_accessible_user_context,
    build_user_from_context,
    get_default_classification_for_role,
)
from backend.prompts.templates import DEPARTMENT_CONTEXTS
import os
import uuid
from datetime import datetime
from typing import Optional

router = APIRouter()

# Initialize services
gemini_service = GeminiService()
document_processor = DocumentProcessor(gemini_service=gemini_service)
report_generator = ReportGenerator(gemini_service)

# Request model for summary generation
class SummaryRequest(BaseModel):
    file_id: str

# In-memory storage for demo (replace with DB later)
# Maps file_id -> FileMetadata
file_metadata_store = {}
# Maps file_id -> file path/type for document processing
file_data_store = {}


async def _get_document_content(file_id: str):
    if file_id not in file_data_store:
        raise HTTPException(status_code=404, detail="File not found")

    file_info = file_data_store[file_id]
    document_content = await document_processor.process_file(file_info["path"], file_info["type"])
    return file_info, document_content


def _get_file_metadata(file_id: str) -> FileMetadata:
    """Retrieve file metadata by ID."""
    if file_id not in file_metadata_store:
        raise HTTPException(status_code=404, detail="File not found")
    return file_metadata_store[file_id]


def _check_file_access(file_id: str, user_context: dict) -> FileMetadata:
    """
    Check if user has access to the file.
    Returns FileMetadata if access is granted, raises 403 otherwise.
    """
    file_metadata = _get_file_metadata(file_id)
    user = build_user_from_context(user_context)
    
    if not can_user_access_file(user, file_metadata):
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: Your role ({user.role.value}) cannot access {file_metadata.classification.value} files"
        )
    
    return file_metadata

@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    classification: Optional[str] = None,
):
    """
    Upload a financial document (PDF, Excel, CSV) with optional classification.
    
    Query/Header Parameters:
    - classification: One of public_company, finance_only, management_only, admin_only
                     Defaults to public_company
    - x-user-role: Optional user role (employee, finance, management, admin)
    - user_id: Optional user ID (for future auth integration)
    """
    # Get authenticated user context from cookie/session
    user_context = get_accessible_user_context(request)
    current_user = build_user_from_context(user_context)
    
    # Validate file type
    allowed_extensions = ['.pdf', '.xlsx', '.xls', '.csv']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Automatically assign classification from logged-in role.
    file_classification = get_default_classification_for_role(current_user.role)
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Save file
    file_path = f"uploads/{file_id}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    uploaded_by = current_user.user_id
    now = datetime.now().isoformat()
    
    # Store metadata
    file_metadata = FileMetadata(
        file_id=file_id,
        filename=file.filename,
        file_type=file_ext,
        size=len(content),
        classification=file_classification,
        uploaded_by=uploaded_by,
        uploaded_at=now,
        is_permanent=True,
        expires_at=None
    )
    file_metadata_store[file_id] = file_metadata
    
    # Store file path and type for document processing
    file_data_store[file_id] = {
        "filename": file.filename,
        "path": file_path,
        "size": len(content),
        "type": file_ext,
        "uploaded_at": now
    }
    
    # Index document for semantic search (RAG)
    try:
        processed_doc = await document_processor.process_file(file_path, file_ext)
        document_text = processed_doc.get("text", "")
        if document_text:
            chunk_count = await rag_service.index_document(document_text, file_id)
            print(f"✨ Indexed document for RAG: {chunk_count} chunks")
    except Exception as e:
        print(f"⚠️  RAG indexing failed: {e}")
        # Continue without RAG - it's non-critical
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file_ext,
        size=len(content),
        message=f"File uploaded successfully with auto-classification: {file_classification.value}"
    )

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    request_http: Request,
    request: AnalysisRequest,
):
    """
    Analyze uploaded document and generate department-specific reports.
    Access controlled based on file classification and user role.
    """
    try:
        # Get authenticated user context from cookie/session
        user_context = get_accessible_user_context(request_http)
        
        # Check access
        _check_file_access(request.file_id, user_context)
        
        file_info, document_content = await _get_document_content(request.file_id)
        
        # Generate reports for each department
        reports = await report_generator.generate_reports(
            document_content,
            request.departments
        )
        
        return AnalysisResponse(
            file_id=request.file_id,
            filename=file_info["filename"],
            raw_analysis=document_content["summary"],
            reports=reports,
            timestamp=datetime.now().isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/chat", response_model=ChatResponse)
async def chat_with_financial_data(
    request_http: Request,
    request: ChatRequest,
):
    """
    Free-form Q&A against uploaded financial data with semantic search.
    Uses RAG (Retrieval-Augmented Generation) to find relevant chunks.
    Access controlled based on file classification and user role.
    """
    try:
        # Get authenticated user context from cookie/session
        user_context = get_accessible_user_context(request_http)
        
        # Check access
        _check_file_access(request.file_id, user_context)
        
        # Get relevant context using RAG semantic search
        rag_context = await rag_service.get_context_for_query(request.file_id, request.question)
        
        # Use fallback to full document if RAG retrieval fails
        _, document_content = await _get_document_content(request.file_id)
        financial_text = document_content.get("text", "")
        
        # If RAG context is available, use it; otherwise use full document
        context_to_use = rag_context if rag_context and rag_context != "No relevant context found." else financial_text
        
        department_focus = ", ".join([d.value for d in request.departments]) if request.departments else "all departments"

        answer = await gemini_service.answer_chat_question(
            financial_data=context_to_use,
            question=request.question,
            department_focus=department_focus,
        )

        return ChatResponse(
            answer=answer,
            timestamp=datetime.now().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@router.post("/studio", response_model=StudioResponse)
async def generate_studio_asset(
    request_http: Request,
    request: StudioRequest,
):
    """
    Generate non-chat assets from the Studio panel with semantic search.
    Uses RAG to retrieve relevant document sections for artifact generation.
    Access controlled based on file classification and user role.
    """
    try:
        # Get authenticated user context from cookie/session
        user_context = get_accessible_user_context(request_http)
        
        # Check access
        _check_file_access(request.file_id, user_context)
        
        # Build search query from asset type and custom prompt
        search_query = f"{request.asset_type.value.replace('_', ' ')} {request.custom_prompt}".strip()
        
        # Get relevant context using RAG semantic search
        rag_context = await rag_service.get_context_for_query(request.file_id, search_query)
        
        # Use fallback to full document if RAG retrieval fails
        _, document_content = await _get_document_content(request.file_id)
        financial_text = document_content.get("text", "")
        
        # If RAG context is available, use it; otherwise use full document
        context_to_use = rag_context if rag_context and rag_context != "No relevant context found." else financial_text

        department_value = request.department.value if request.department else "all"
        department_context = DEPARTMENT_CONTEXTS.get(department_value, "")
        custom_prompt = request.custom_prompt or ""

        content = await gemini_service.generate_studio_asset(
            financial_data=context_to_use,
            asset_type=request.asset_type.value,
            department=department_value,
            custom_prompt=f"{custom_prompt}\n\nDepartment Context:\n{department_context}",
        )

        title = f"{request.asset_type.value.replace('_', ' ').title()}"
        if department_value != "all":
            title = f"{title} - {department_value.title()}"

        return StudioResponse(
            asset_type=request.asset_type,
            title=title,
            content=content,
            timestamp=datetime.now().isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Studio generation failed: {str(e)}")

@router.get("/reports/{file_id}")
async def get_report(
    request: Request,
    file_id: str,
):
    """
    Get metadata for a specific file.
    Access controlled based on file classification and user role.
    """
    # Get authenticated user context from cookie/session
    user_context = get_accessible_user_context(request)
    
    # Check access
    file_metadata = _check_file_access(file_id, user_context)
    
    return file_metadata.dict()


@router.post("/generate-summary")
async def generate_summary(
    request_http: Request,
    request: SummaryRequest,
):
    """
    Generate an AI summary of an uploaded document.
    Returns a concise summary that captures key information.
    """
    try:
        # Get authenticated user context from cookie/session
        user_context = get_accessible_user_context(request_http)
        
        # Check access
        _check_file_access(request.file_id, user_context)
        
        # Get document content
        _, document_content = await _get_document_content(request.file_id)
        document_text = document_content.get("text", "")
        
        if not document_text or len(document_text.strip()) < 10:
            raise HTTPException(
                status_code=400, 
                detail="Document has no extractable text. This may be because: 1) The PDF is image-based and OCR quota is exhausted, 2) The file is corrupted, or 3) The file format is not supported. Try a text-based PDF or wait for API quota to reset."
            )

        # console.log(f"Generating summary for file_id: {request.file_id}, text length: {len(document_text)}")
        # Generate summary using Gemini
        summary = await gemini_service.generate_document_summary(document_text)
        
        return {
            "file_id": request.file_id,
            # "summary": summary + document_text[:500],  # Include a snippet of original text for reference
            "summary": summary,  # Include a snippet of original text for reference
            "generated_at": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summary generation failed: {str(e)}")


@router.post("/upload-managed", response_model=UploadResponse)
async def upload_managed_document(
    request: Request,
    file: UploadFile = File(...),
    classification: Optional[str] = None,
    title: Optional[str] = None,
    storage_mode: Optional[str] = "full",
    auto_delete: Optional[bool] = False,
    summary: Optional[str] = None,
):
    """
    Upload a document with advanced management options.
    
    Parameters:
    - file: The document file to upload
    - classification: Access level (public_company, finance_only, management_only, admin_only)
    - title: Custom title for the document
    - storage_mode: "full" (store entire document) or "summary" (store only AI summary)
    - auto_delete: If true, file will be deleted after 7 days
    - summary: Pre-generated summary text (if storage_mode is "summary")
    - x-user-role: User role for access control
    - user_id: User ID for tracking
    """
    from datetime import timedelta
    
    # Get authenticated user context from cookie/session
    user_context = get_accessible_user_context(request)
    current_user = build_user_from_context(user_context)
    
    # Validate file type
    allowed_extensions = ['.pdf', '.xlsx', '.xls', '.csv']
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Automatically assign classification from logged-in role.
    file_classification = get_default_classification_for_role(current_user.role)
    
    # Validate storage mode
    if storage_mode not in ["full", "summary"]:
        raise HTTPException(
            status_code=400,
            detail="storage_mode must be 'full' or 'summary'"
        )
    
    # Generate unique file ID
    file_id = str(uuid.uuid4())
    
    # Save file
    file_path = f"uploads/{file_id}_{file.filename}"
    os.makedirs("uploads", exist_ok=True)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    uploaded_by = current_user.user_id
    now = datetime.now()
    
    # Calculate expiry if auto_delete is enabled
    expires_at = None
    if auto_delete:
        expires_at = (now + timedelta(days=7)).isoformat()
    
    # Process document
    processed_doc = await document_processor.process_file(file_path, file_ext)
    document_text = processed_doc.get("text", "")
    
    # Determine what to store and index for RAG
    if storage_mode == "summary":
        if not summary:
            raise HTTPException(
                status_code=400,
                detail="Summary text is required when storage_mode is 'summary'"
            )
        # Index the summary for RAG instead of full document
        text_to_index = summary
    else:
        # Index full document
        text_to_index = document_text
    
    # Index for semantic search (RAG)
    try:
        if text_to_index:
            chunk_count = await rag_service.index_document(text_to_index, file_id)
            print(f"✨ Indexed document for RAG: {chunk_count} chunks (mode: {storage_mode})")
    except Exception as e:
        print(f"⚠️  RAG indexing failed: {e}")
        # Continue without RAG - it's non-critical
    
    # Store metadata with extended fields
    file_metadata = FileMetadata(
        file_id=file_id,
        filename=title or file.filename,
        file_type=file_ext,
        size=len(content),
        classification=file_classification,
        uploaded_by=uploaded_by,
        uploaded_at=now.isoformat(),
        is_permanent=not auto_delete,
        expires_at=expires_at
    )
    file_metadata_store[file_id] = file_metadata
    
    # Store file path and additional metadata
    file_data_store[file_id] = {
        "filename": file.filename,
        "path": file_path,
        "size": len(content),
        "type": file_ext,
        "uploaded_at": now.isoformat(),
        "storage_mode": storage_mode,
        "summary": summary if storage_mode == "summary" else None
    }
    
    return UploadResponse(
        file_id=file_id,
        filename=title or file.filename,
        file_type=file_ext,
        size=len(content),
        message=f"File uploaded successfully with auto-classification: {file_classification.value} (mode: {storage_mode})"
    )
