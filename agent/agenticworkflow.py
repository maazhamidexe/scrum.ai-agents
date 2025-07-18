from langgraph.graph import StateGraph, END, START
from agentic.utils.model_loader import load_model
from agentic.prompt_library.prompt import SYSTEM_PROMPT
import datetime
import time
import json
import uuid

# Tool imports
from agentic.tool.firebase_tool import (
    write_project_summary, get_dev_profiles, create_ticket, 
    get_project_tickets, get_scrum_history, save_scrum_cycle_summary,
    get_project_config, update_project_config
)
from agentic.tool.vector_retriever import get_vector_retriever
from agentic.tool.scrum_timer import (
    is_scrum_time_reached, get_cycle_timing_info, set_cycle_start_time
)
from agentic.tool.standup_fetcher import (
    get_all_standups, get_standup_status, get_standup_summary_data
)
from agentic.tool.ticket_generator import (
    generate_project_tickets, analyze_developer_workload, 
    optimize_ticket_assignment, create_sprint_plan
)
from agentic.utils.firebase_client import get_firestore

# Agent helpers
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.prompts import ChatPromptTemplate


class ScrumGraphBuilder:
    def __init__(self, model_provider="groq"):
        self.llm = load_model()
        self.system_prompt = SYSTEM_PROMPT
        
        # Set up all tools
        self.tools = [
            write_project_summary, get_dev_profiles, create_ticket, 
            get_project_tickets, get_scrum_history, save_scrum_cycle_summary,
            get_project_config, update_project_config,
            is_scrum_time_reached, get_cycle_timing_info, set_cycle_start_time,
            get_all_standups, get_standup_status, get_standup_summary_data,
            generate_project_tickets, analyze_developer_workload, 
            optimize_ticket_assignment, create_sprint_plan
        ]

        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.graph = None

    def _log(self, message):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"[SCRUM-WORKFLOW][{now}] {message}")

    def store_project_context_node(self, state):
        self._log("Entering node: StoreProjectContext")
        start_time = time.time()
        from agentic.utils.text_splitter import split_project_markdown
        from agentic.utils.embedding import embed_documents
        from agentic.utils.pinecone_client import init_pinecone

        project_id = state["project_id"]
        project_description = state["project_description"]
        
        # Split and embed project description
        docs = split_project_markdown(project_description)
        vectors = embed_documents(docs)
        index = init_pinecone()
        namespace = project_id
        
        # Store in Pinecone
        for i, doc in enumerate(docs):
            index.upsert(vectors=[{
                "id": f"{namespace}-{i}",
                "values": vectors[i],
                "metadata": {"text": doc.page_content}
            }], namespace=namespace)

        # --- Use LLM to generate a project summary ---
        summary_prompt = f"""
        Summarize the following project description for a software engineering team. Focus on the main goals, features, and technical stack. Be concise and clear.
        
        Project Description:
        {project_description}
        """
        summary_response = self.llm.invoke(summary_prompt)
        summary = summary_response.content.strip()
        write_project_summary.invoke({"project_id": project_id, "summary": summary})
        
        # Initialize project configuration
        update_project_config.invoke({"project_id": project_id, "scrum_cycle_duration_minutes": 1440, "max_cycles": 10})
        
        state["project_summary"] = summary
        state["vector_stored"] = True
        state["next_node"] = "gather_context"
        
        self._log(f"Project summary: {summary[:120]}{'...' if len(summary) > 120 else ''}")
        elapsed = time.time() - start_time
        self._log(f"Exiting node: StoreProjectContext (took {elapsed:.2f}s)")
        return state

    def gather_context_node(self, state):
        self._log("Entering node: GatherContext")
        start_time = time.time()
        project_id = state["project_id"]
        
        # Get developer profiles
        dev_profiles = get_dev_profiles.invoke({"project_id": project_id})
        
        # Get project configuration
        project_config = get_project_config.invoke({"project_id": project_id})
        
        # Get scrum history
        scrum_history = get_scrum_history.invoke({"project_id": project_id, "limit": 5})
        
        # Get existing tickets
        existing_tickets = get_project_tickets.invoke({"project_id": project_id})
        
        # Store context in state
        state["dev_profiles"] = dev_profiles
        state["project_config"] = project_config
        state["scrum_history"] = scrum_history
        state["existing_tickets"] = existing_tickets
        state["context_gathered"] = True
        state["next_node"] = "generate_tickets"
        
        self._log("Gathering developer profiles, project config, scrum history, and existing tickets")
        elapsed = time.time() - start_time
        self._log(f"Exiting node: GatherContext (took {elapsed:.2f}s)")
        return state

    def generate_tickets_node(self, state):
        self._log("Entering node: GenerateTickets")
        start_time = time.time()
        project_id = state["project_id"]
        project_description = state["project_description"]
        dev_profiles = state["dev_profiles"]
        scrum_cycle_duration = state["project_config"].get("scrum_cycle_duration_minutes", 1440) // 60  # Convert to hours

        # --- Get project context from Pinecone ---
        retriever = get_vector_retriever(project_id)
        # Limit to top 3 relevant docs
        if hasattr(retriever, "invoke"):
            project_context_docs = retriever.invoke(project_description, k=3)
        else:
            try:
                project_context_docs = retriever.get_relevant_documents(project_description, k=3)
            except TypeError:
                project_context_docs = retriever.get_relevant_documents(project_description)[:3]
        # Truncate each doc to 300 chars
        project_context = "\n".join([doc.page_content[:300] for doc in project_context_docs])

        # --- Prepare LLM prompt for ticket generation ---
        llm_ticket_prompt = f"""
        You are a Scrum Master AI. Given the following project context and developer profiles, break down the project into actionable tickets for each developer.
        
        STRICT INSTRUCTIONS:
        - ONLY return a valid JSON object mapping dev_id to a list of tickets for that developer.
        - DO NOT include any explanation, markdown, or extra text before or after the JSON.
        - Each ticket must have: title, description, priority (high/medium/low), estimated_hours.
        - Use the project context for technical and feature details.
        - Use developer skills and roles to assign relevant tickets.
        - If you do not know what to assign, return an empty list for that dev_id.
        - WARNING: Any extra text, explanation, or formatting will break the system.
        
        Project Context:
        {project_context}
        
        Developer Profiles:
        {json.dumps(dev_profiles, indent=2)}
        
        Example output (and ONLY this, no explanation):
        {{
          "dev1": [{{"title": "Setup project structure", "description": "Initialize the repo and dependencies", "priority": "high", "estimated_hours": 4}}],
          "dev2": [{{"title": "Implement backend API", "description": "Create FastAPI endpoints", "priority": "high", "estimated_hours": 8}}],
          "dev3": []
        }}
        """
        llm_response = self.llm.invoke(llm_ticket_prompt)
        try:
            dev_ticket_map = json.loads(llm_response.content)
        except Exception:
            # fallback: try to extract JSON from the response
            import re
            match = re.search(r'\{[\s\S]*\}', llm_response.content)
            if match:
                dev_ticket_map = json.loads(match.group(0))
            else:
                dev_ticket_map = {}

        # --- Store tickets in Firestore under each dev's subcollection ---
        db = get_firestore()
        created_tickets = []
        ticket_assignments = {}  # dev_id -> list of ticket dicts
        for dev_id, tickets in dev_ticket_map.items():
            ticket_assignments[dev_id] = []
            for ticket in tickets:
                ticket_id = str(uuid.uuid4())
                ticket_doc = {
                    "id": ticket_id,
                    "title": ticket.get("title", ""),
                    "description": ticket.get("description", ""),
                    "priority": ticket.get("priority", "medium"),
                    "estimated_hours": ticket.get("estimated_hours", 8),
                    "assigned_dev_id": dev_id,
                    "status": "todo",
                    "created_at": datetime.datetime.now(datetime.timezone.utc),
                    "updated_at": datetime.datetime.now(datetime.timezone.utc)
                }
                # Store in dev_profiles/{dev_id}/tickets
                db.collection("projects").document(project_id).collection("dev_profiles").document(dev_id).collection("tickets").document(ticket_id).set(ticket_doc)
                created_tickets.append(ticket_doc)
                ticket_assignments[dev_id].append(ticket_doc)
        state["generated_tickets"] = created_tickets
        state["ticket_assignments"] = ticket_assignments
        state["tickets_created"] = True
        state["next_node"] = "wait_for_standups"
        self._log(f"Tickets generated: {sum(len(v) for v in ticket_assignments.values())}")
        elapsed = time.time() - start_time
        self._log(f"Exiting node: GenerateTickets (took {elapsed:.2f}s)")
        return state

    def wait_for_standups_node(self, state):
        self._log("Entering node: WaitForStandups")
        start_time = time.time()
        project_id = state["project_id"]
        current_cycle = state["scrum_cycle"]
        
        # Set cycle start time if this is the first cycle
        if current_cycle == 0:
            set_cycle_start_time.invoke({"project_id": project_id, "cycle_number": current_cycle})
        
        # Wait loop - check for standup completion or time expiration
        max_wait_time = 300  # 5 minutes for demo purposes
        wait_interval = 30   # Check every 30 seconds
        waited_time = 0
        
        while waited_time < max_wait_time:
            # Check standup status
            standup_status = get_standup_status.invoke({"project_id": project_id, "cycle_number": current_cycle})
            
            # Check if time is reached
            timing_info = get_cycle_timing_info.invoke({"project_id": project_id})
            
            # If all standups submitted or time reached, proceed
            if standup_status["is_complete"] or timing_info["is_time_reached"]:
                break
            
            time.sleep(wait_interval)
            waited_time += wait_interval
        
        state["standup_status"] = standup_status
        state["timing_info"] = timing_info
        state["standups_ready"] = True
        state["next_node"] = "summarize_standups"
        self._log(f"Standup status: {standup_status}")
        self._log(f"Timing info: {timing_info}")
        elapsed = time.time() - start_time
        self._log(f"Exiting node: WaitForStandups (took {elapsed:.2f}s)")
        return state

    def summarize_standups_node(self, state):
        self._log("Entering node: SummarizeStandups")
        start_time = time.time()
        project_id = state["project_id"]
        current_cycle = state["scrum_cycle"]

        # Get all standup data for summarization (current cycle)
        standup_data = get_standup_summary_data.invoke({"project_id": project_id, "cycle_number": current_cycle})

        # Fetch project summary
        db = get_firestore()
        project_doc = db.collection("projects").document(project_id).get()
        project_summary = project_doc.to_dict().get("summary", "") if project_doc.exists else ""

        # Fetch last 5 scrum cycle summaries
        scrum_history = get_scrum_history.invoke({"project_id": project_id, "limit": 5})
        scrum_history_str = "\n".join([
            f"Cycle {c.get('cycle_number', '?')}: {c.get('summary', '')}" for c in scrum_history
        ]) if scrum_history else "No previous cycles."

        # Fetch all tickets
        all_tickets = get_project_tickets.invoke({"project_id": project_id})
        all_tickets_str = "\n".join([
            f"{t.get('title', '')} (Assigned: {t.get('assigned_dev_id', '')}, Status: {t.get('status', '')})" for t in all_tickets
        ]) if all_tickets else "No tickets."

        # Fetch all standups (all cycles)
        all_standups = []
        standups_collection = db.collection("projects").document(project_id).collection("standups").stream()
        for doc in standups_collection:
            all_standups.append(doc.to_dict())
        all_standups_str = "\n".join([
            f"Cycle {s.get('cycle', '?')} - {s.get('dev_id', '')}: {s.get('text', s.get('yesterday_work', ''))}" for s in all_standups
        ]) if all_standups else "No standups."

        # Create summarization prompt
        summary_prompt = f"""
Project Summary:\n{project_summary}\n\nScrum History (last 5 cycles):\n{scrum_history_str}\n\nAll Tickets:\n{all_tickets_str}\n\nAll Standups (all cycles):\n{all_standups_str}\n\nCurrent Cycle ({current_cycle}) Standups:\n{standup_data['standups']}\nCurrent Cycle Tickets:\n{standup_data['tickets']}\n\nProvide a comprehensive summary including:\n1. Overall progress made\n2. Key achievements\n3. Blockers and issues\n4. Next steps and priorities\n5. Team velocity insights\n"""

        # Generate summary using LLM
        summary_response = self.llm.invoke(summary_prompt)
        summary = summary_response.content

        # Get participant list
        participants = [standup.get("dev_id") for standup in standup_data["standups"]]

        # Calculate metrics
        metrics = {
            "total_standups": standup_data["total_standups"],
            "cycle_number": current_cycle,
            "completion_rate": len(participants) / len(state["dev_profiles"]) * 100 if state["dev_profiles"] else 0
        }

        # Save scrum cycle summary, including ticket_assignments
        save_scrum_cycle_summary.invoke({
            "project_id": project_id,
            "cycle_number": current_cycle,
            "summary": summary,
            "participants": participants,
            "metrics": metrics,
            "ticket_assignments": state.get("ticket_assignments", {})
        })

        state["cycle_summary"] = summary
        state["cycle_metrics"] = metrics
        state["summary_saved"] = True
        state["next_node"] = "manage_cycle"
        self._log(f"Summary generated (first 120 chars): {summary[:120]}{'...' if len(summary) > 120 else ''}")
        elapsed = time.time() - start_time
        self._log(f"Exiting node: SummarizeStandups (took {elapsed:.2f}s)")
        return state

    def manage_cycle_node(self, state):
        self._log("Entering node: ManageCycle")
        start_time = time.time()
        project_id = state["project_id"]
        current_cycle = state["scrum_cycle"]
        
        # Get project configuration
        project_config = state["project_config"]
        max_cycles = project_config.get("max_cycles", 10)
        
        # Increment cycle
        state["scrum_cycle"] += 1
        new_cycle = state["scrum_cycle"]
        
        # Check if project should continue
        if new_cycle >= max_cycles:
            state["done"] = True
            state["next_node"] = "end"
        else:
            # Continue to next cycle
            state["next_node"] = "wait_for_standups"
        
        self._log("Managing cycle progression and determining next steps")
        elapsed = time.time() - start_time
        self._log(f"Exiting node: ManageCycle (took {elapsed:.2f}s)")
        return state

    def build_graph(self):
        self._log("Initiating ScrumGraphBuilder workflow graph construction")
        start_time = time.time()
        graph_builder = StateGraph(dict)

        # Add all nodes
        graph_builder.add_node("StoreProjectContext", self.store_project_context_node)
        graph_builder.add_node("GatherContext", self.gather_context_node)
        graph_builder.add_node("GenerateTickets", self.generate_tickets_node)
        graph_builder.add_node("WaitForStandups", self.wait_for_standups_node)
        graph_builder.add_node("SummarizeStandups", self.summarize_standups_node)
        graph_builder.add_node("ManageCycle", self.manage_cycle_node)

        # Set entry point
        graph_builder.set_entry_point("StoreProjectContext")

        # Add edges based on next_node logic
        def route_to_next(state):
            next_node = state.get("next_node", "end")
            if next_node == "end" or state.get("done", False):
                return "End"
            return next_node

        # Add conditional edges
        graph_builder.add_conditional_edges("StoreProjectContext", lambda s: "GatherContext")
        graph_builder.add_conditional_edges("GatherContext", lambda s: "GenerateTickets")
        graph_builder.add_conditional_edges("GenerateTickets", lambda s: "WaitForStandups")
        graph_builder.add_conditional_edges("WaitForStandups", lambda s: "SummarizeStandups")
        graph_builder.add_conditional_edges("SummarizeStandups", lambda s: "ManageCycle")
        graph_builder.add_conditional_edges("ManageCycle", route_to_next)

        # Add end node
        graph_builder.add_node("End", lambda x: x)

        self.graph = graph_builder.compile()
        elapsed = time.time() - start_time
        self._log(f"Workflow graph constructed (took {elapsed:.2f}s)")
        return self.graph

    def __call__(self):
        self._log("ScrumGraphBuilder workflow initiated")
        return self.build_graph()
