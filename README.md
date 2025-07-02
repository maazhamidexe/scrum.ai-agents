# 🧠 AI Scrum Master – LLM-Powered Agile Assistant

This project is a modular, LangGraph-based backend system that simulates the role of a **Scrum Master** using LLM agents. It enables Agile teams to automatically run standups, detect blockers, analyze retrospectives, plan upcoming sprints, and summarize progress – all via API.

## 🔧 Features

- 🤖 **LLM Agents**: LangChain tools and LangGraph for modular multi-step reasoning
- 📊 **Standup Summarizer**: Converts daily standups into structured summaries
- 🚧 **Blocker Detector**: Flags stuck team members or unresolved issues
- 🧠 **Retrospective Analyzer**: Processes retro notes into team insights
- 📅 **Sprint Planner**: Auto-selects next sprint tasks based on remaining backlog
- 📈 **Sprint Summary**: Final report with total tasks completed and highlights
- 🌐 **FastAPI Backend**: Easily consumable endpoint to integrate into Slack, dashboards, etc.


## 🚀 How It Works

The backend flows through these steps in sequence via a LangGraph:

1. `start`: Initializes the graph state
2. `summarize`: Generates standup summaries
3. `check_blockers`: Extracts team blockers
4. `retrospective`: Analyzes team feedback
5. `sprint_planner`: Plans the next sprint
6. `summarize_sprint`: Generates a final report

The output is a structured `suggestions` list ready to display or feed to a dashboard.

## 🛠️ API Usage

### Endpoint


## 🚀 How It Works

The backend flows through these steps in sequence via a LangGraph:

1. `start`: Initializes the graph state
2. `summarize`: Generates standup summaries
3. `check_blockers`: Extracts team blockers
4. `retrospective`: Analyzes team feedback
5. `sprint_planner`: Plans the next sprint
6. `summarize_sprint`: Generates a final report

The output is a structured `suggestions` list ready to display or feed to a dashboard.

## 🛠️ API Usage

### Endpoint

POST /run-scrum

bash
Copy
Edit

### Example Payload

```json
{
  "standups": [
    "I completed the login flow",
    "I’m stuck on the payment API",
    "Nothing blocking me"
  ],
  "retros": [
    "We need better testing coverage",
    "Team communication was great"
  ],
  "sprint_tasks": [
    "Build dashboard", "Fix API rate limit", "Write tests", "Refactor auth"
  ],
  "completed_tasks": [
    "Fix API rate limit"
  ]
}
Response
json
Copy
Edit
{
  "output": [
    "Summary:\n- I completed the login flow\n- I’m stuck on the payment API\n- Nothing blocking me",
    "Retrospective:\nRetro: We need better testing coverage\nRetro: Team communication was great",
    "Next Sprint Plan: [\"Build dashboard\", \"Write tests\", \"Refactor auth\"]",
    "Sprint completed 1 tasks."
  ]
}
📦 Install & Run
bash
Copy
Edit
pip install -r requirements.txt
uvicorn main:app --reload
🧩 Tech Stack
Python

FastAPI

LangGraph (LangChain)

Pydantic

OpenAI (optional, replaceable)POST /run-scrum

bash
Copy
Edit

### Example Payload

```json
{
  "standups": [
    "I completed the login flow",
    "I’m stuck on the payment API",
    "Nothing blocking me"
  ],
  "retros": [
    "We need better testing coverage",
    "Team communication was great"
  ],
  "sprint_tasks": [
    "Build dashboard", "Fix API rate limit", "Write tests", "Refactor auth"
  ],
  "completed_tasks": [
    "Fix API rate limit"
  ]
}
Response
json
Copy
Edit
{
  "output": [
    "Summary:\n- I completed the login flow\n- I’m stuck on the payment API\n- Nothing blocking me",
    "Retrospective:\nRetro: We need better testing coverage\nRetro: Team communication was great",
    "Next Sprint Plan: [\"Build dashboard\", \"Write tests\", \"Refactor auth\"]",
    "Sprint completed 1 tasks."
  ]
}
📦 Install & Run
bash
Copy
Edit
pip install -r requirements.txt
uvicorn main:app --reload
🧩 Tech Stack
Python

FastAPI

LangGraph (LangChain)

Pydantic

OpenAI (optional, replaceable)
