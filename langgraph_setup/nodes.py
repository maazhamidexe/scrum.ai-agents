
from langchain.agents import tool

# --- Tool definitions ---
@tool
def summarize_standups(standups):
    return "\n".join([f"- {s}" for s in standups])

@tool
def detect_blockers(standups):
    return [s for s in standups if "blocker" in s.lower() or "stuck" in s.lower()]

@tool
def analyze_retros(retros):
    return "\n".join([f"Retro: {r}" for r in retros])

@tool
def plan_next_sprint(sprint_tasks, completed_tasks):
    return [t for t in sprint_tasks if t not in completed_tasks][:5]

@tool
def generate_sprint_summary(completed_tasks):
    return f"Sprint completed {len(completed_tasks)} tasks."

# --- Graph nodes ---
def start(state):
    return state

def summarize(state):
    summary = summarize_standups(state['standups'])
    state['suggestions'].append(f"Summary:\n{summary}")
    return state

def check_blockers(state):
    blockers = detect_blockers(state['standups'])
    state['blockers'].extend(blockers)
    return state

def retrospective(state):
    analysis = analyze_retros(state['retros'])
    state['suggestions'].append(f"Retrospective:\n{analysis}")
    return state

def sprint_planner(state):
    plan = plan_next_sprint(state['sprint_tasks'], state['completed_tasks'])
    state['suggestions'].append(f"Next Sprint Plan: {plan}")
    return state

def summarize_sprint(state):
    report = generate_sprint_summary(state['completed_tasks'])
    state['suggestions'].append(report)
    return state