"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def is_announcement_active(announcement: Dict[str, Any]) -> bool:
    """Check if announcement is currently active based on dates"""
    now = datetime.now()
    
    # Check expiration date (required)
    expiration = datetime.fromisoformat(announcement.get("expiration_date", ""))
    if now > expiration:
        return False
    
    # Check start date (optional)
    if "start_date" in announcement and announcement["start_date"]:
        start = datetime.fromisoformat(announcement["start_date"])
        if now < start:
            return False
    
    return True


@router.get("/active")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all currently active announcements"""
    announcements = list(announcements_collection.find())
    
    # Filter to only active announcements
    active_announcements = []
    for announcement in announcements:
        if is_announcement_active(announcement):
            announcement["_id"] = str(announcement["_id"])
            active_announcements.append(announcement)
    
    return active_announcements


@router.get("")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    announcements = list(announcements_collection.find())
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
        # Add active status
        announcement["is_active"] = is_announcement_active(announcement)
    
    return announcements


@router.post("")
def create_announcement(
    message: str,
    expiration_date: str,
    username: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate expiration date
    try:
        exp_date = datetime.fromisoformat(expiration_date)
        if exp_date <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="Expiration date must be in the future"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration date format"
        )
    
    # Validate start date if provided
    if start_date:
        try:
            datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start date format"
            )
    
    # Create announcement document
    announcement = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": username,
        "created_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return {
        "message": "Announcement created successfully",
        "announcement": announcement
    }


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str,
    message: str,
    expiration_date: str,
    username: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate announcement exists
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    existing = announcements_collection.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Validate expiration date
    try:
        exp_date = datetime.fromisoformat(expiration_date)
        if exp_date <= datetime.now():
            raise HTTPException(
                status_code=400,
                detail="Expiration date must be in the future"
            )
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid expiration date format"
        )
    
    # Validate start date if provided
    if start_date:
        try:
            datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid start date format"
            )
    
    # Update announcement
    updated_data = {
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "updated_by": username,
        "updated_at": datetime.now().isoformat()
    }
    
    announcements_collection.update_one(
        {"_id": obj_id},
        {"$set": updated_data}
    )
    
    return {"message": "Announcement updated successfully"}


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, Any]:
    """Delete an announcement (requires authentication)"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate and delete announcement
    try:
        obj_id = ObjectId(announcement_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
