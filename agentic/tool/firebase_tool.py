from langchain.tools import tool
from agentic.utils.firebase_client import get_firestore
import datetime
import uuid
import sys

db = get_firestore()

@tool
def write_project_summary(project_id: str, summary: str):
    """Store a short summary for the given project in Firestore."""
    db.collection("projects").document(project_id).update({
        "summary": summary,
        "created_at": datetime.datetime.utcnow(),
        "status": "active"
    })
    return f"Summary saved for {project_id}"

@tool
def get_dev_profiles(project_id: str):
    """Retrieve the developer profiles for a given project from Firestore."""
    docs = db.collection("projects").document(project_id).collection("dev_profiles").stream()
    return [doc.to_dict() for doc in docs]

@tool
def create_ticket(project_id: str, title: str, description: str, assigned_dev_id: str, priority: str = "medium", estimated_hours: int = 8):
    """Create a new ticket in Firebase for the given project and assign it to a developer."""
    ticket_id = str(uuid.uuid4())
    ticket_data = {
        "id": ticket_id,
        "title": title,
        "description": description,
        "assigned_dev_id": assigned_dev_id,
        "priority": priority,
        "estimated_hours": estimated_hours,
        "status": "todo",
        "created_at": datetime.datetime.utcnow(),
        "updated_at": datetime.datetime.utcnow()
    }
    
    db.collection("projects").document(project_id).collection("tickets").document(ticket_id).set(ticket_data)
    return f"Ticket '{title}' created and assigned to dev {assigned_dev_id}"

@tool
def get_project_tickets(project_id: str, status: str = None):
    """Get all tickets for a project, optionally filtered by status."""
    query = db.collection("projects").document(project_id).collection("tickets")
    if status:
        query = query.where("status", "==", status)
    
    docs = query.stream()
    return [doc.to_dict() for doc in docs]

@tool
def get_scrum_history(project_id: str, limit: int = 5):
    """Get recent scrum cycle summaries for the project."""
    docs = db.collection("projects").document(project_id).collection("scrum_cycles").order_by("cycle_number", direction="DESCENDING").limit(limit).stream()
    return [doc.to_dict() for doc in docs]

@tool
def save_scrum_cycle_summary(project_id: str, cycle_number: int, summary: str, participants: list, metrics: dict = None):
    """Save a scrum cycle summary to Firebase."""
    # Truncate summary if too long
    if len(summary) > 5000:
        summary = summary[:5000] + '... (truncated)'
    # Truncate participants if too many
    if len(participants) > 100:
        participants = participants[:100]
    cycle_data = {
        "cycle_number": cycle_number,
        "summary": summary,
        "participants": participants,
        "metrics": metrics or {},
        "timestamp": datetime.datetime.utcnow()
    }
    print(f"[DEBUG] Saving scrum cycle summary, size: {sys.getsizeof(str(cycle_data))} bytes")
    db.collection("projects").document(project_id).collection("scrum_cycles").document(f"cycle_{cycle_number}").set(cycle_data)
    # Update project with last scrum timestamp
    db.collection("projects").document(project_id).update({
        "last_scrum_timestamp": datetime.datetime.utcnow(),
        "current_cycle": cycle_number
    })
    return f"Scrum cycle {cycle_number} summary saved"

@tool
def get_project_config(project_id: str):
    """Get project configuration including scrum cycle duration and other settings."""
    doc = db.collection("projects").document(project_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

@tool
def update_project_config(project_id: str, scrum_cycle_duration_minutes: int = 1440, max_cycles: int = 10):
    """Update project configuration with scrum settings."""
    config = {
        "scrum_cycle_duration_minutes": scrum_cycle_duration_minutes,
        "max_cycles": max_cycles,
        "updated_at": datetime.datetime.utcnow()
    }
    
    db.collection("projects").document(project_id).update(config)
    return f"Project config updated for {project_id}"
