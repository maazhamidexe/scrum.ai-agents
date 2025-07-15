from langchain.tools import tool
import datetime
from agentic.utils.firebase_client import get_firestore

@tool
def is_scrum_time_reached(project_id: str) -> bool:
    """check if the scrum time is reached for the given project"""
    db = get_firestore()
    doc = db.collection("projects").document(project_id).get().to_dict()
    last_cycle_time = doc.get("last_scrum_timestamp")
    duration_minutes = doc.get("scrum_cycle_duration", 1440)  # default: 1 day

    if not last_cycle_time:
        return True

    last_time = last_cycle_time.timestamp()
    now = datetime.datetime.utcnow().timestamp()
    return (now - last_time) > (duration_minutes * 60)
