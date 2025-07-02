
from langgraph.graph import StateGraph
from langgraph_setup.nodes import (
    start, summarize, check_blockers, retrospective, sprint_planner, summarize_sprint
)
from typing import TypedDict, List

class ScrumState(TypedDict):
    standups: List[str]
    blockers: List[str]
    retros: List[str]
    sprint_tasks: List[str]
    completed_tasks: List[str]
    suggestions: List[str]

# Build the graph
def run_scrum_graph(state: ScrumState):
    graph = StateGraph(ScrumState)
    graph.set_entry_point(start)
    graph.add_node("summarize", summarize)
    graph.add_node("check_blockers", check_blockers)
    graph.add_node("retrospective", retrospective)
    graph.add_node("sprint_planner", sprint_planner)
    graph.add_node("summarize_sprint", summarize_sprint)

    graph.add_edge(start, summarize)
    graph.add_edge(summarize, check_blockers)
    graph.add_edge(check_blockers, retrospective)
    graph.add_edge(retrospective, sprint_planner)
    graph.add_edge(sprint_planner, summarize_sprint)
    graph.add_edge(summarize_sprint, graph.end)

    app_graph = graph.compile()
    return app_graph.invoke(state)