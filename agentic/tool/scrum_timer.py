from langchain.tools import tool
import datetime
from agentic.utils.firebase_client import get_firestore

@tool
def is_scrum_time_reached(project_id: str) -> bool:
    """Check if the scrum time is reached for the given project"""
    db = get_firestore()
    doc = db.collection("projects").document(project_id).get()
    if not doc.exists:
        return True
    
    project_data = doc.to_dict()
    last_cycle_time = project_data.get("last_scrum_timestamp")
    duration_minutes = project_data.get("scrum_cycle_duration_minutes", 1440)  # default: 1 day

    if not last_cycle_time:
        return True

    # Convert to datetime if it's a timestamp
    if isinstance(last_cycle_time, datetime.datetime):
        if last_cycle_time.tzinfo is None:
            last_time = last_cycle_time.replace(tzinfo=datetime.timezone.utc)
        else:
            last_time = last_cycle_time
    else:
        last_time = datetime.datetime.fromtimestamp(last_cycle_time, tz=datetime.timezone.utc)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    time_diff = now - last_time
    minutes_passed = time_diff.total_seconds() / 60
    
    return minutes_passed >= duration_minutes

@tool
def get_cycle_timing_info(project_id: str) -> dict:
    """Get detailed timing information for the current scrum cycle"""
    db = get_firestore()
    doc = db.collection("projects").document(project_id).get()
    if not doc.exists:
        return {"error": "Project not found"}
    
    project_data = doc.to_dict()
    last_cycle_time = project_data.get("last_scrum_timestamp")
    duration_minutes = project_data.get("scrum_cycle_duration_minutes", 1440)
    current_cycle = project_data.get("current_cycle", 0)
    
    if not last_cycle_time:
        return {
            "current_cycle": current_cycle,
            "cycle_duration_minutes": duration_minutes,
            "time_remaining_minutes": duration_minutes,
            "is_time_reached": True,
            "last_cycle_time": None
        }
    
    # Convert to datetime if it's a timestamp
    if isinstance(last_cycle_time, datetime.datetime):
        if last_cycle_time.tzinfo is None:
            last_time = last_cycle_time.replace(tzinfo=datetime.timezone.utc)
        else:
            last_time = last_cycle_time
    else:
        last_time = datetime.datetime.fromtimestamp(last_cycle_time, tz=datetime.timezone.utc)
    
    now = datetime.datetime.now(datetime.timezone.utc)
    time_diff = now - last_time
    minutes_passed = time_diff.total_seconds() / 60
    time_remaining = max(0, duration_minutes - minutes_passed)
    
    return {
        "current_cycle": current_cycle,
        "cycle_duration_minutes": duration_minutes,
        "minutes_passed": minutes_passed,
        "time_remaining_minutes": time_remaining,
        "is_time_reached": minutes_passed >= duration_minutes,
        "last_cycle_time": last_time.isoformat(),
        "next_cycle_time": (last_time + datetime.timedelta(minutes=duration_minutes)).isoformat()
    }

@tool
def set_cycle_start_time(project_id: str, cycle_number: int):
    """Set the start time for a new scrum cycle"""
    db = get_firestore()
    now = datetime.datetime.now(datetime.timezone.utc)
    
    db.collection("projects").document(project_id).update({
        "last_scrum_timestamp": now,
        "current_cycle": cycle_number,
        "cycle_start_time": now
    })
    
    return f"Cycle {cycle_number} start time set for {project_id}"
