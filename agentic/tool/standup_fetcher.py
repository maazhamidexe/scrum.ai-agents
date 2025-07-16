from langchain.tools import tool
from agentic.utils.firebase_client import get_firestore
import datetime

@tool
def get_all_standups(project_id: str, cycle_number: int):
    """Get all standups for the given project and cycle number"""
    db = get_firestore()
    docs = db.collection("projects")\
             .document(project_id)\
             .collection("standups")\
             .where("cycle", "==", cycle_number).stream()
    return [doc.to_dict() for doc in docs]

@tool
def get_standup_status(project_id: str, cycle_number: int):
    """Get the status of standups for a specific cycle - who has submitted and who hasn't"""
    db = get_firestore()
    
    # Get all developers for the project
    dev_docs = db.collection("projects").document(project_id).collection("dev_profiles").stream()
    all_devs = [doc.to_dict() for doc in dev_docs]
    
    # Get submitted standups for this cycle
    standup_docs = db.collection("projects")\
                    .document(project_id)\
                    .collection("standups")\
                    .where("cycle", "==", cycle_number).stream()
    submitted_standups = [doc.to_dict() for doc in standup_docs]
    
    # Create status report
    submitted_dev_ids = [s.get("dev_id") for s in submitted_standups]
    missing_devs = [dev for dev in all_devs if dev.get("id") not in submitted_dev_ids]
    
    return {
        "cycle_number": cycle_number,
        "total_developers": len(all_devs),
        "submitted_standups": len(submitted_standups),
        "missing_standups": len(missing_devs),
        "submitted_devs": [s.get("dev_id") for s in submitted_standups],
        "missing_devs": [dev.get("id") for dev in missing_devs],
        "is_complete": len(submitted_standups) >= len(all_devs)
    }

@tool
def create_standup_template(project_id: str, cycle_number: int, dev_id: str):
    """Create a standup template for a developer in a specific cycle"""
    db = get_firestore()
    
    # Get current tickets for this developer
    ticket_docs = db.collection("projects").document(project_id).collection("tickets")\
                   .where("assigned_dev_id", "==", dev_id)\
                   .where("status", "in", ["in_progress", "todo"]).stream()
    current_tickets = [doc.to_dict() for doc in ticket_docs]
    
    template = {
        "cycle": cycle_number,
        "dev_id": dev_id,
        "timestamp": datetime.datetime.utcnow(),
        "yesterday_work": "",
        "today_plan": "",
        "blockers": "",
        "ticket_updates": [],
        "status": "draft"
    }
    
    # Add current tickets to template
    for ticket in current_tickets:
        template["ticket_updates"].append({
            "ticket_id": ticket.get("id"),
            "ticket_title": ticket.get("title"),
            "status": ticket.get("status"),
            "progress_notes": ""
        })
    
    return template

@tool
def save_standup(project_id: str, cycle_number: int, dev_id: str, standup_data: dict):
    """Save a completed standup for a developer"""
    db = get_firestore()
    
    standup_data.update({
        "cycle": cycle_number,
        "dev_id": dev_id,
        "timestamp": datetime.datetime.utcnow(),
        "status": "completed"
    })
    
    # Save to Firebase
    doc_id = f"{dev_id}_cycle_{cycle_number}"
    db.collection("projects").document(project_id).collection("standups").document(doc_id).set(standup_data)
    
    return f"Standup saved for dev {dev_id} in cycle {cycle_number}"

@tool
def get_standup_summary_data(project_id: str, cycle_number: int):
    """Get all standup data formatted for summarization"""
    db = get_firestore()
    
    # Get all standups for this cycle
    standup_docs = db.collection("projects")\
                    .document(project_id)\
                    .collection("standups")\
                    .where("cycle", "==", cycle_number).stream()
    standups = [doc.to_dict() for doc in standup_docs]
    
    # Get current tickets for context
    ticket_docs = db.collection("projects").document(project_id).collection("tickets").stream()
    tickets = [doc.to_dict() for doc in ticket_docs]
    
    # Format data for summarization
    summary_data = {
        "cycle_number": cycle_number,
        "total_standups": len(standups),
        "standups": standups,
        "tickets": tickets,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    
    return summary_data
