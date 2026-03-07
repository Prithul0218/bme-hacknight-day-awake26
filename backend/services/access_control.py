"""
Access Control Service
Manages file access based on user roles and file classifications.
Extensible for future authentication/authorization enhancements.
"""

from backend.models.schemas import User, Role, FileMetadata, FileClassification
from backend.services.auth_service import get_user_by_id
from fastapi import Request, HTTPException


def can_user_access_file(user: User, file_metadata: FileMetadata) -> bool:
    """
    Determines if a user can access a specific file based on their role
    and the file's classification.
    
    Access Matrix:
    - PUBLIC_COMPANY: All employees (EMPLOYEE, FINANCE, MANAGEMENT, ADMIN)
    - FINANCE_ONLY: Finance and Admin roles only
    - MANAGEMENT_ONLY: Management and Admin roles only
    - ADMIN_ONLY: Admin role only
    
    Args:
        user: User object with role information
        file_metadata: FileMetadata object with classification
        
    Returns:
        bool: True if user can access the file, False otherwise
    """
    
    if not user.is_active:
        return False
    
    # Admin role can access everything
    if user.role == Role.ADMIN:
        return True
    
    # Public company data is accessible to all active users
    if file_metadata.classification == FileClassification.PUBLIC_COMPANY:
        return True
    
    # Finance-only data accessible to finance and admin roles
    if file_metadata.classification == FileClassification.FINANCE_ONLY:
        return user.role in [Role.FINANCE, Role.ADMIN]
    
    # Management-only data accessible to management and admin roles
    if file_metadata.classification == FileClassification.MANAGEMENT_ONLY:
        return user.role in [Role.MANAGEMENT, Role.ADMIN]
    
    # Admin-only data accessible to admin role only
    if file_metadata.classification == FileClassification.ADMIN_ONLY:
        return user.role == Role.ADMIN
    
    return False


def get_accessible_user_context(request: Request) -> dict:
    """
    Returns user context for the current session.
    This is a placeholder that will be replaced with actual auth (JWT, session, etc).
    
    For now, returns a default test user that can be overridden via environment
    or headers in the future.
    
    Returns:
        dict: User context with user_id, name, role, department
    """
    user_id = request.cookies.get("auth_user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = get_user_by_id(user_id)
    if not user or not bool(user.get("is_active", True)):
        raise HTTPException(status_code=401, detail="Invalid or inactive user")

    return {
        "user_id": user.get("user_id"),
        "name": user.get("name"),
        "role": user.get("role", Role.EMPLOYEE.value),
        "department": user.get("department"),
    }


def get_default_classification_for_role(role: Role) -> FileClassification:
    """Map role to the default classification used for automatic access-level selection."""
    if role == Role.ADMIN:
        return FileClassification.ADMIN_ONLY
    if role == Role.MANAGEMENT:
        return FileClassification.MANAGEMENT_ONLY
    if role == Role.FINANCE:
        return FileClassification.FINANCE_ONLY
    return FileClassification.PUBLIC_COMPANY


def build_user_from_context(user_context: dict) -> User:
    """
    Constructs a User object from context dictionary.
    
    Args:
        user_context: Dictionary with user_id, name, role, department
        
    Returns:
        User: User object with validated role
    """
    return User(
        user_id=user_context.get("user_id", "unknown"),
        name=user_context.get("name", "Unknown User"),
        role=Role(user_context.get("role", Role.EMPLOYEE.value)),
        department=user_context.get("department")
    )
