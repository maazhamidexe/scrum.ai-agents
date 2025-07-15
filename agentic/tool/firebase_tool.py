from langchain.tools import tool
from agentic.utils.firebase_client import get_firestore

db = get_firestore()

@tool
def write_project_summary(project_id: str, summary: str):
    """Store a short summary for the given project in Firestore."""
    db.collection("projects").document(project_id).update({
        "summary": summary
    })
    return f"Summary saved for {project_id}"

@tool
def get_dev_profiles(project_id: str):
    """Retrieve the developer profiles for a given project from Firestore."""
    docs = db.collection("projects").document(project_id).collection("dev_profiles").stream()
    return [doc.to_dict() for doc in docs]
