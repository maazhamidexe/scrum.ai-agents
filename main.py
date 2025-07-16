import uuid
from agent.agenticworkflow import ScrumGraphBuilder
from agentic.utils.firebase_client import get_firestore
from agentic.tool.firebase_tool import get_project_tickets
import datetime

# --- Project and Developer Setup ---
def create_sample_dev_profiles():
    return [
        {
            "id": "dev1",
            "name": "Alice",
            "tech": ["React", "TypeScript", "Next.js"],
            "role": "Frontend Developer",
            "experience_years": 4
        },
        {
            "id": "dev2",
            "name": "Bob",
            "tech": ["Python", "FastAPI", "Firebase"],
            "role": "Backend Developer",
            "experience_years": 5
        },
        {
            "id": "dev3",
            "name": "Carol",
            "tech": ["UI/UX", "Figma", "CSS"],
            "role": "Designer",
            "experience_years": 3
        }
    ]

def setup_project_in_firestore(project_id, dev_profiles):
    db = get_firestore()
    # Create project doc if not exists
    project_ref = db.collection("projects").document(project_id)
    if not project_ref.get().exists:
        project_ref.set({"id": project_id, "status": "active"})
    # Add dev profiles
    for dev in dev_profiles:
        dev_ref = project_ref.collection("dev_profiles").document(dev["id"])
        if not dev_ref.get().exists:
            dev_ref.set(dev)

# --- Simulate developer standups ---
def insert_sample_standups(project_id, cycle, dev_profiles):
    db = get_firestore()
    standups = [
        {
            "dev_id": dev["id"],
            "cycle": cycle,
            "text": f"Yesterday I worked on my assigned tickets. Today I will continue. No blockers.",
            "timestamp": datetime.datetime.now(datetime.timezone.utc),
            "status": "completed"
        }
        for dev in dev_profiles
    ]
    for standup in standups:
        doc_id = f"{standup['dev_id']}_cycle_{cycle}"
        db.collection("projects").document(project_id).collection("standups").document(doc_id).set(standup)
    print(f"Inserted {len(standups)} standups for cycle {cycle}.")

# --- Main Workflow ---
def main():
    # Use a unique project_id for each run
    project_id = f"proj-{uuid.uuid4().hex[:8]}"
    dev_profiles = create_sample_dev_profiles()
    setup_project_in_firestore(project_id, dev_profiles)

    # Detailed, real-world project description
    project_description = """
Project Title: Smart Remote Work Collaboration Platform

Project Summary:
Build a web-based platform to help distributed software teams collaborate efficiently. The platform should support:
- Real-time chat and video calls
- Kanban-style task boards
- Automated daily standup reminders and summaries
- Integration with GitHub for PR and issue tracking
- Team mood tracking and anonymous feedback
- Secure authentication (Google, GitHub)

Features:
1. User registration and authentication (Google, GitHub OAuth)
2. Team creation and invitation system
3. Real-time chat rooms and video calls (WebRTC)
4. Kanban board for project/task management
5. Automated daily standup bot (collects, summarizes, posts to channel)
6. GitHub integration: show open PRs/issues, link commits to tasks
7. Mood tracking: daily anonymous survey, team dashboard
8. Responsive UI/UX for desktop and mobile

Tech Stack:
- Frontend: React, Next.js, Tailwind CSS
- Backend: FastAPI, Firebase Firestore
- Real-time: WebSockets, WebRTC
- Auth: Firebase Auth, OAuth
- Integrations: GitHub API
- Deployment: Vercel, Google Cloud

Development Phases:
1. Auth & Team setup
2. Chat & video
3. Kanban board
4. Standup bot
5. GitHub integration
6. Mood tracking
7. Polish & deploy
"""

    # --- Run the agentic workflow for the first cycle ---
    workflow = ScrumGraphBuilder()
    graph = workflow()
    initial_state = {
        "project_id": project_id,
        "project_description": project_description,
        "scrum_cycle": 0,
        "done": False
    }

    print(f"\n🚀 Starting Scrum AI workflow for project: {project_id}")
    print("=" * 60)
    # Run the workflow up to ticket generation
    result = graph.invoke(initial_state)

    # --- Simulate standup submissions for cycle 0 ---
    insert_sample_standups(project_id, 0, dev_profiles)

    # --- Resume the workflow to process standups and generate summary ---
    # The workflow will sense the standups, summarize, and start a new cycle
    result = graph.invoke({
        **result,
        "done": False  # allow next cycle
    })

    # --- Print the summary for the first cycle ---
    db = get_firestore()
    scrum_cycle_doc = db.collection("projects").document(project_id).collection("scrum_cycles").document("cycle_0").get()
    if scrum_cycle_doc.exists:
        print("\n📊 Scrum Cycle 0 Summary:")
        print(scrum_cycle_doc.to_dict().get("summary", "No summary found."))
    else:
        print("No scrum cycle 0 summary found.")

    # --- Print tickets for each developer for the next cycle ---
    print("\n📝 Tickets generated and assigned to developers for next cycle:")
    dev_profiles_docs = db.collection("projects").document(project_id).collection("dev_profiles").stream()
    found = False
    for dev_doc in dev_profiles_docs:
        dev_id = dev_doc.id
        tickets_ref = db.collection("projects").document(project_id).collection("dev_profiles").document(dev_id).collection("tickets")
        tickets = [t.to_dict() for t in tickets_ref.stream()]
        if tickets:
            found = True
            print(f"\nTickets for {dev_doc.to_dict().get('name', dev_id)} ({dev_id}):")
            for t in tickets:
                print(f"- {t.get('title')}: {t.get('description')} (Priority: {t.get('priority')}, Est. hours: {t.get('estimated_hours')})")
    if not found:
        print("No tickets found.")

    print("\n✅ Workflow complete.\n")

if __name__ == "__main__":
    main()
