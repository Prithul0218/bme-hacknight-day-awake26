"""
Access Control Service
Manages file access based on user roles and file classifications.
Extensible for future authentication/authorization enhancements.
"""

from backend.models.schemas import User, Role, FileMetadata, FileClassification


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


def get_accessible_user_context() -> dict:
    """
    Returns user context for the current session.
    This is a placeholder that will be replaced with actual auth (JWT, session, etc).
    
    For now, returns a default test user that can be overridden via environment
    or headers in the future.
    
    Returns:
        dict: User context with user_id, name, role, department
    """
    # TODO: Replace with actual JWT/session authentication
    # For now, default to an employee user
    # This can be overridden by:
    # 1. Environment variables
    # 2. Request headers (X-User-ID, X-User-Role)
    # 3. JWT token validation
    
    return {
        "user_id": "user_default",
        "name": "Current User",
        "role": Role.EMPLOYEE,
        "department": None
    }


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
