from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from langgraph_setup.graph import run_scrum_graph

app = FastAPI()

class ScrumInput(BaseModel):
    standups: List[str]
    retros: List[str]
    sprint_tasks: List[str]
    completed_tasks: List[str]

@app.post("/run-scrum")
def run_scrum(input_data: ScrumInput):
    initial_state = {
        'standups': input_data.standups,
        'retros': input_data.retros,
        'sprint_tasks': input_data.sprint_tasks,
        'completed_tasks': input_data.completed_tasks,
        'blockers': [],
        'suggestions': []
    }
    result = run_scrum_graph(initial_state)
    return {"output": result['suggestions']}