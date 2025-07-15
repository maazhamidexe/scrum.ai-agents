from langchain.tools import tool
from agentic.utils.firebase_client import get_firestore

@tool
def get_all_standups(project_id: str, cycle_number: int):
    """get all standups for the given project and cycle number"""
    db = get_firestore()
    docs = db.collection("projects")\
             .document(project_id)\
             .collection("standups")\
             .where("cycle", "==", cycle_number).stream()
    return [doc.to_dict() for doc in docs]
