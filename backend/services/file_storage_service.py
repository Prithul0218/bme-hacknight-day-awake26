"""
File Storage Service
Handles persistent JSON storage of file metadata and summaries
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FILES_DB_PATH = DATA_DIR / "files.json"

def ensure_data_dir():
    """Ensure data directory exists"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def load_files_database() -> Dict:
    """Load all files from JSON database"""
    ensure_data_dir()
    
    if not FILES_DB_PATH.exists():
        return {"files": {}}
    
    try:
        with open(FILES_DB_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  Failed to load files database: {e}")
        return {"files": {}}

def save_files_database(data: Dict):
    """Save files database to JSON"""
    ensure_data_dir()
    
    try:
        with open(FILES_DB_PATH, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"❌ Failed to save files database: {e}")

def add_file(
    file_id: str,
    filename: str,
    file_type: str,
    size: int,
    classification: str,
    uploaded_by: str,
    file_path: str,
    ai_summary: str = "",
    file_type_category: str = "permanent",  # "permanent" or "temporary"
    is_permanent: bool = True,
    expires_at: Optional[str] = None,
) -> bool:
    """Add or update a file in the database"""
    try:
        data = load_files_database()
        
        data["files"][file_id] = {
            "file_id": file_id,
            "filename": filename,
            "file_type": file_type,
            "size": size,
            "classification": classification,
            "uploaded_by": uploaded_by,
            "file_path": file_path,
            "ai_summary": ai_summary,  # Short summary under 50 words
            "file_type_category": file_type_category,
            "is_permanent": is_permanent,
            "expires_at": expires_at,
            "uploaded_at": datetime.now().isoformat(),
        }
        
        save_files_database(data)
        return True
    except Exception as e:
        print(f"❌ Failed to add file: {e}")
        return False

def get_file(file_id: str) -> Optional[Dict]:
    """Get a specific file by ID"""
    data = load_files_database()
    return data.get("files", {}).get(file_id)

def get_all_files() -> Dict:
    """Get all files"""
    data = load_files_database()
    return data.get("files", {})

def get_user_files(user_id: str) -> List[Dict]:
    """Get all files uploaded by a specific user"""
    data = load_files_database()
    files = data.get("files", {})
    
    user_files = []
    for file_id, file_info in files.items():
        if file_info.get("uploaded_by") == user_id:
            user_files.append(file_info)
    
    return sorted(user_files, key=lambda x: x.get("uploaded_at", ""), reverse=True)

def get_files_of_type(file_type_category: str) -> List[Dict]:
    """Get all files of a specific type (temporary/permanent)"""
    data = load_files_database()
    files = data.get("files", {})
    
    category_files = []
    for file_id, file_info in files.items():
        if file_info.get("file_type_category") == file_type_category:
            category_files.append(file_info)
    
    return sorted(category_files, key=lambda x: x.get("uploaded_at", ""), reverse=True)

def delete_file(file_id: str) -> bool:
    """Delete a file from database (physical file deletion handled separately)"""
    try:
        data = load_files_database()
        files = data.get("files", {})
        
        if file_id in files:
            del files[file_id]
            save_files_database(data)
            return True
        
        return False
    except Exception as e:
        print(f"❌ Failed to delete file: {e}")
        return False

def update_file_summary(file_id: str, ai_summary: str) -> bool:
    """Update the AI summary for a file"""
    try:
        data = load_files_database()
        files = data.get("files", {})
        
        if file_id in files:
            files[file_id]["ai_summary"] = ai_summary
            save_files_database(data)
            return True
        
        return False
    except Exception as e:
        print(f"❌ Failed to update file summary: {e}")
        return False
