from agent.agenticworkflow import ScrumGraphBuilder

workflow = ScrumGraphBuilder()
graph = workflow()

initial_state = {
    "project_id": "proj-123",
    "project_description": "Build an e-commerce analytics dashboard using Firebase and React.",
    "project_summary": "",
    "vector_context": [],
    "dev_profiles": [{"name": "Ali", "tech": "React"}, {"name": "Sara", "tech": "Firebase"}],
    "tickets": [],
    "standups": [],
    "scrum_cycle": 0,
    "scrum_summary": [],
    "done": False
}

result = graph.invoke(initial_state)
print(result)
