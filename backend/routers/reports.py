from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse
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
    can_user_assign_classification,
    get_accessible_user_context,
    build_user_from_context,
    get_default_classification_for_role,
)
from backend.prompts.templates import DEPARTMENT_CONTEXTS
from backend.services.file_storage_service import (
    load_files_database,
    add_file,
    get_file,
    get_all_files,
    get_user_files,
    delete_file as delete_file_from_storage,
    update_file_summary,
)
import os
import mimetypes
import uuid
from datetime import datetime
from typing import Optional, List

router = APIRouter()

# Initialize services
gemini_service = GeminiService()
document_processor = DocumentProcessor(gemini_service=gemini_service)
report_generator = ReportGenerator(gemini_service)

# Request model for summary generation
class SummaryRequest(BaseModel):
    file_id: str

# In-memory cache for runtime performance (synced with JSON on startup/shutdown)
# Maps file_id -> FileMetadata
file_metadata_store = {}
# Maps file_id -> file path/type for document processing
file_data_store = {}

def load_files_from_json():
    """Load all files from JSON database into memory cache"""
    global file_metadata_store, file_data_store
    
    files_db = load_files_database()
    files = files_db.get("files", {})
    
    for file_id, file_info in files.items():
        # Reconstruct metadata
        from backend.models.schemas import FileMetadata
        
        file_metadata_store[file_id] = FileMetadata(
            file_id=file_id,
            filename=file_info.get("filename", ""),
            file_type=file_info.get("file_type", ""),
            size=file_info.get("size", 0),
            classification=file_info.get("classification", "public_company"),
            uploaded_by=file_info.get("uploaded_by", ""),
            uploaded_at=file_info.get("uploaded_at", ""),
            is_permanent=file_info.get("is_permanent", True),
            expires_at=file_info.get("expires_at"),
        )
        
        # Reconstruct file data
        file_data_store[file_id] = {
            "filename": file_info.get("filename", ""),
            "path": file_info.get("file_path", ""),
            "size": file_info.get("size", 0),
            "type": file_info.get("file_type", ""),
            "uploaded_at": file_info.get("uploaded_at", ""),
            "ai_summary": file_info.get("ai_summary", ""),
        }
    
    print(f"📂 Loaded {len(file_metadata_store)} files from JSON database")


async def generate_short_ai_summary(document_text: str) -> str:
    """
    Generate a short AI title for a document.
    Returns a concise title-like description of what the document contains.
    """
    try:
        if not document_text or len(document_text.strip()) < 20:
            return "No content available"
        
        prompt = f"""Create a title on what this document contains under 15 words. Don't add company name. Nothing else.

Document:
{document_text[:1000]}"""
        
        response = await gemini_service._generate_content(prompt)
        summary = response.text
        # Keep title concise
        words = summary.split()[:50]
        return " ".join(words)
    except Exception as e:
        print(f"⚠️  Failed to generate short AI title: {e}")
        return "Document uploaded successfully"


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
    temporary: bool = False,
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
    
    # Auto-select classification from role, but allow explicit override from UI.
    file_classification = get_default_classification_for_role(current_user.role)
    if classification:
        try:
            requested_classification = FileClassification(classification)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid classification. Must be one of: public_company, finance_only, management_only, admin_only",
            )

        if not can_user_assign_classification(current_user.role, requested_classification):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Access denied: Your role ({current_user.role.value}) cannot upload files "
                    f"with {requested_classification.value} classification"
                ),
            )

        file_classification = requested_classification
    
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
        is_permanent=not temporary,
        expires_at=None
    )
    file_metadata_store[file_id] = file_metadata
    
    # Store file path and type for document processing
    file_data_store[file_id] = {
        "filename": file.filename,
        "path": file_path,
        "size": len(content),
        "type": file_ext,
        "uploaded_at": now,
        "ai_summary": ""  # Will be populated below
    }
    
    # Process document and generate short AI summary
    short_summary = ""
    try:
        processed_doc = await document_processor.process_file(file_path, file_ext)
        document_text = processed_doc.get("text", "")
        
        if document_text:
            # Generate short AI summary (under 50 words)
            short_summary = await generate_short_ai_summary(document_text)
            file_data_store[file_id]["ai_summary"] = short_summary
            
            # Index document for semantic search (RAG)
            chunk_count = await rag_service.index_document(document_text, file_id)
            print(f"✨ Indexed document for RAG: {chunk_count} chunks")
    except Exception as e:
        print(f"⚠️  Processing failed: {e}")
        # Continue without processing - it's non-critical
    
    # Save to JSON database for persistence
    add_file(
        file_id=file_id,
        filename=file.filename,
        file_type=file_ext,
        size=len(content),
        classification=file_classification.value,
        uploaded_by=uploaded_by,
        file_path=file_path,
        ai_summary=short_summary,
        file_type_category="temporary" if temporary else "permanent",
        is_permanent=not temporary,
        expires_at=None
    )
    
    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_type=file_ext,
        size=len(content),
        message=f"File uploaded successfully with auto-classification: {file_classification.value}",
        ai_title=short_summary or None,
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


@router.get("/user-files")
async def get_user_files(request: Request):
    """
    Get all files the current user has access to.
    Returns accessible company-managed (permanent) files and user temporary files.
    """
    try:
        user_context = get_accessible_user_context(request)
        user = build_user_from_context(user_context)
        
        # Get all files from database
        from backend.services.file_storage_service import get_all_files
        all_files = get_all_files()
        
        accessible_files = []
        temporary_files = []
        for file_id, file_info in all_files.items():
            # Create metadata object for access check
            file_metadata = FileMetadata(
                file_id=file_id,
                filename=file_info.get("filename", ""),
                file_type=file_info.get("file_type", ""),
                size=file_info.get("size", 0),
                classification=FileClassification(file_info.get("classification", "public_company")),
                uploaded_by=file_info.get("uploaded_by", ""),
                uploaded_at=file_info.get("uploaded_at", ""),
                is_permanent=file_info.get("is_permanent", True),
                expires_at=file_info.get("expires_at"),
            )
            
            # Check if user can access this file
            if can_user_access_file(user, file_metadata):
                file_payload = {
                    "file_id": file_id,
                    "filename": file_info.get("filename"),
                    "ai_title": file_info.get("ai_summary", ""),
                    "ai_summary": file_info.get("ai_summary", ""),
                    "size": file_info.get("size", 0),
                    "classification": file_info.get("classification"),
                    "uploaded_at": file_info.get("uploaded_at"),
                }

                if file_info.get("file_type_category") == "temporary":
                    # Temporary docs are scoped to the uploader's workspace session.
                    if file_info.get("uploaded_by") == user.user_id:
                        temporary_files.append(file_payload)
                else:
                    accessible_files.append(file_payload)

        accessible_files = sorted(
            accessible_files,
            key=lambda item: item.get("uploaded_at", ""),
            reverse=True,
        )
        temporary_files = sorted(
            temporary_files,
            key=lambda item: item.get("uploaded_at", ""),
            reverse=True,
        )
        
        return {
            "user_id": user.user_id,
            "role": user.role.value,
            "files": accessible_files,
            "temporary_files": temporary_files,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user files: {str(e)}")


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

        # Support chat with multiple temp docs, single temp doc, or no temp docs.
        target_ids: List[str] = []
        if request.file_ids:
            target_ids.extend([fid for fid in request.file_ids if fid])
        if request.file_id:
            target_ids.append(request.file_id)
        # Keep order while removing duplicates.
        target_ids = list(dict.fromkeys(target_ids))

        contexts: List[str] = []
        valid_files: List[str] = []
        skipped_files: List[str] = []

        for file_id in target_ids:
            # Skip missing/forbidden files instead of failing the whole chat.
            try:
                _check_file_access(file_id, user_context)
                rag_context = await rag_service.get_context_for_query(file_id, request.question)
                _, document_content = await _get_document_content(file_id)
                financial_text = document_content.get("text", "")
                selected_context = (
                    rag_context if rag_context and rag_context != "No relevant context found." else financial_text
                )
                if selected_context and selected_context.strip():
                    contexts.append(selected_context.strip())
                valid_files.append(file_id)
            except HTTPException:
                skipped_files.append(file_id)
            except Exception:
                skipped_files.append(file_id)

        if contexts:
            context_to_use = "\n\n---\n\n".join(contexts)
        else:
            # Baseline context allows chat continuity even with no uploaded docs.
            context_to_use = (
                "No temporary financial documents are currently loaded. "
                "Provide a concise, practical answer based on general finance best practices "
                "and clearly state that the guidance is not tied to uploaded company data."
            )
        
        department_focus = ", ".join([d.value for d in request.departments]) if request.departments else "all departments"

        answer = await gemini_service.answer_chat_question(
            financial_data=context_to_use,
            question=request.question,
            department_focus=department_focus,
        )

        if skipped_files and valid_files:
            answer = (
                answer
                + "\n\nNote: Some previously uploaded temporary files were unavailable and were skipped."
            )
        elif skipped_files and not valid_files:
            answer = (
                answer
                + "\n\nNote: Previously uploaded temporary files were unavailable, so this response is based on general guidance."
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
    
    # Auto-select classification from role, but allow explicit override from UI.
    file_classification = get_default_classification_for_role(current_user.role)
    if classification:
        try:
            requested_classification = FileClassification(classification)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid classification. Must be one of: public_company, finance_only, management_only, admin_only",
            )

        if not can_user_assign_classification(current_user.role, requested_classification):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Access denied: Your role ({current_user.role.value}) cannot upload files "
                    f"with {requested_classification.value} classification"
                ),
            )

        file_classification = requested_classification
    
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
    
    # Process document and generate short AI summary
    processed_doc = await document_processor.process_file(file_path, file_ext)
    document_text = processed_doc.get("text", "")
    
    # Generate short summary (under 50 words)
    short_summary = ""
    try:
        short_summary = await generate_short_ai_summary(document_text)
    except Exception as e:
        print(f"⚠️  Failed to generate short summary: {e}")
        short_summary = ""
    
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
        "summary": summary if storage_mode == "summary" else None,
        "ai_summary": short_summary
    }
    
    # Save to JSON database for persistence
    add_file(
        file_id=file_id,
        filename=title or file.filename,
        file_type=file_ext,
        size=len(content),
        classification=file_classification.value,
        uploaded_by=uploaded_by,
        file_path=file_path,
        ai_summary=short_summary,
        file_type_category="permanent",
        is_permanent=not auto_delete,
        expires_at=expires_at
    )
    
    return UploadResponse(
        file_id=file_id,
        filename=title or file.filename,
        file_type=file_ext,
        size=len(content),
        message=f"File uploaded successfully with auto-classification: {file_classification.value} (mode: {storage_mode})",
        ai_title=short_summary or None,
    )


@router.get("/file/{file_id}/open")
async def open_file(
    request: Request,
    file_id: str,
):
    """
    Open a file in-browser/new tab for users with access to that file.
    """
    try:
        user_context = get_accessible_user_context(request)
        _check_file_access(file_id, user_context)

        if file_id not in file_data_store:
            raise HTTPException(status_code=404, detail="File not found")

        file_info = file_data_store[file_id]
        file_path = file_info.get("path", "")
        filename = file_info.get("filename", "document")

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found on disk")

        media_type, _ = mimetypes.guess_type(filename)
        return FileResponse(
            path=file_path,
            media_type=media_type or "application/octet-stream",
            filename=filename,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to open file: {str(e)}")


@router.delete("/file/{file_id}")
async def delete_uploaded_file(
    request: Request,
    file_id: str,
):
    """
    Delete a file uploaded by the current user.
    Only the user who uploaded the file can delete it.
    Removes file from disk and metadata store.
    """
    try:
        # Get authenticated user context from cookie/session
        user_context = get_accessible_user_context(request)
        current_user = build_user_from_context(user_context)
        
        # Check if file exists
        if file_id not in file_metadata_store:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_metadata = file_metadata_store[file_id]
        
        # Check if current user is the owner
        if file_metadata.uploaded_by != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="You can only delete files you uploaded"
            )
        
        # Delete physical file
        if file_id in file_data_store:
            file_info = file_data_store[file_id]
            file_path = file_info["path"]
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"⚠️  Failed to delete physical file {file_path}: {e}")
                # Continue with metadata deletion anyway
        
        # Delete from metadata store
        del file_metadata_store[file_id]
        
        # Delete from data store
        if file_id in file_data_store:
            del file_data_store[file_id]
        
        # Delete from JSON database
        delete_file_from_storage(file_id)
        
        return {
            "success": True,
            "message": f"File deleted successfully",
            "file_id": file_id
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File deletion failed: {str(e)}")
