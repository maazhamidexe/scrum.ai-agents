from langchain.tools import tool
from agentic.utils.firebase_client import get_firestore
from agentic.tool.vector_retriever import get_vector_retriever
from agentic.tool.firebase_tool import get_scrum_history, get_project_tickets
import json

@tool
def generate_project_tickets(project_id: str, project_description: str, dev_profiles: list, scrum_cycle_duration_hours: int = 24):
    """Generate comprehensive tickets for a project based on description, developer skills, and scrum cycle duration"""
    
    # Get project context from vector store
    retriever = get_vector_retriever(project_id)
    
    # Get relevant project context
    # Use .invoke for retriever if available (to avoid deprecation warning)
    if hasattr(retriever, "invoke"):
        context_docs = retriever.invoke(project_description)
    else:
        context_docs = retriever.get_relevant_documents(project_description)
    project_context = "\n".join([doc.page_content for doc in context_docs])
    
    # Get scrum history for context (use .invoke)
    scrum_history = get_scrum_history.invoke({"project_id": project_id, "limit": 3})
    
    # Get existing tickets to avoid duplication
    existing_tickets = get_project_tickets.invoke({"project_id": project_id})
    
    # Create ticket generation context
    generation_context = {
        "project_description": project_description,
        "project_context": project_context,
        "developer_profiles": dev_profiles,
        "scrum_cycle_duration_hours": scrum_cycle_duration_hours,
        "scrum_history": scrum_history,
        "existing_tickets": existing_tickets
    }
    
    return generation_context

@tool
def analyze_developer_workload(project_id: str, dev_id: str):
    """Analyze the current workload and progress of a specific developer"""
    db = get_firestore()
    
    # Get all tickets assigned to this developer
    ticket_docs = db.collection("projects").document(project_id).collection("tickets")\
                   .where("assigned_dev_id", "==", dev_id).stream()
    tickets = [doc.to_dict() for doc in ticket_docs]
    
    # Calculate workload metrics
    total_tickets = len(tickets)
    completed_tickets = len([t for t in tickets if t.get("status") == "completed"])
    in_progress_tickets = len([t for t in tickets if t.get("status") == "in_progress"])
    todo_tickets = len([t for t in tickets if t.get("status") == "todo"])
    
    total_estimated_hours = sum([t.get("estimated_hours", 0) for t in tickets])
    completed_hours = sum([t.get("estimated_hours", 0) for t in tickets if t.get("status") == "completed"])
    
    # Get recent standups for this developer
    standup_docs = db.collection("projects").document(project_id).collection("standups")\
                    .where("dev_id", "==", dev_id)\
                    .order_by("timestamp", direction="DESCENDING").limit(3).stream()
    recent_standups = [doc.to_dict() for doc in standup_docs]
    
    workload_analysis = {
        "dev_id": dev_id,
        "total_tickets": total_tickets,
        "completed_tickets": completed_tickets,
        "in_progress_tickets": in_progress_tickets,
        "todo_tickets": todo_tickets,
        "completion_rate": (completed_tickets / total_tickets * 100) if total_tickets > 0 else 0,
        "total_estimated_hours": total_estimated_hours,
        "completed_hours": completed_hours,
        "hours_completion_rate": (completed_hours / total_estimated_hours * 100) if total_estimated_hours > 0 else 0,
        "recent_standups": recent_standups,
        "current_workload": "high" if todo_tickets > 3 else "medium" if todo_tickets > 1 else "low"
    }
    
    return workload_analysis

@tool
def optimize_ticket_assignment(project_id: str, tickets_to_assign: list):
    """Optimize ticket assignment based on developer skills, workload, and availability"""
    db = get_firestore()
    
    # Get all developers and their current workload
    dev_docs = db.collection("projects").document(project_id).collection("dev_profiles").stream()
    developers = [doc.to_dict() for doc in dev_docs]
    
    # Analyze workload for each developer
    dev_workloads = {}
    for dev in developers:
        dev_id = dev.get("id")
        workload = analyze_developer_workload(project_id, dev_id)
        dev_workloads[dev_id] = workload
    
    # Create assignment recommendations
    assignments = []
    for ticket in tickets_to_assign:
        best_dev = None
        best_score = -1
        
        for dev in developers:
            dev_id = dev.get("id")
            workload = dev_workloads[dev_id]
            
            # Calculate assignment score based on:
            # 1. Skill match (if ticket has tech requirements)
            # 2. Current workload (prefer developers with lower workload)
            # 3. Completion rate (prefer developers with good track record)
            
            skill_match = 1.0  # Default score
            if ticket.get("tech_requirements"):
                dev_skills = dev.get("tech", [])
                if isinstance(dev_skills, str):
                    dev_skills = [dev_skills]
                if ticket.get("tech_requirements") in dev_skills:
                    skill_match = 2.0
            
            workload_score = 1.0 - (workload.get("todo_tickets", 0) * 0.2)  # Reduce score for high workload
            completion_score = workload.get("completion_rate", 0) / 100
            
            total_score = skill_match + workload_score + completion_score
            
            if total_score > best_score:
                best_score = total_score
                best_dev = dev_id
        
        assignments.append({
            "ticket": ticket,
            "assigned_dev_id": best_dev,
            "assignment_score": best_score,
            "reasoning": f"Best match based on skills, workload ({dev_workloads[best_dev]['current_workload']}), and completion rate ({dev_workloads[best_dev]['completion_rate']:.1f}%)"
        })
    
    return assignments

@tool
def create_sprint_plan(project_id: str, sprint_duration_days: int = 14):
    """Create a comprehensive sprint plan with tickets, assignments, and timeline"""
    
    # Get project context
    db = get_firestore()
    project_doc = db.collection("projects").document(project_id).get()
    if not project_doc.exists:
        return {"error": "Project not found"}
    
    project_data = project_doc.to_dict()
    project_description = project_data.get("summary", "")
    
    # Get developer profiles
    dev_docs = db.collection("projects").document(project_id).collection("dev_profiles").stream()
    developers = [doc.to_dict() for doc in dev_docs]
    
    # Get existing tickets
    existing_tickets = get_project_tickets.invoke({"project_id": project_id})
    
    # Calculate sprint capacity
    total_dev_hours = len(developers) * sprint_duration_days * 8  # Assuming 8 hours per day
    available_hours = total_dev_hours * 0.7  # 70% capacity for actual development
    
    # Create sprint plan
    sprint_plan = {
        "project_id": project_id,
        "sprint_duration_days": sprint_duration_days,
        "total_dev_hours": total_dev_hours,
        "available_hours": available_hours,
        "developers": developers,
        "existing_tickets": existing_tickets,
        "sprint_goals": [],
        "ticket_assignments": [],
        "timeline": {
            "start_date": None,  # Will be set when sprint starts
            "end_date": None,
            "milestones": []
        }
    }
    
    return sprint_plan