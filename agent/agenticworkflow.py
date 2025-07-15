from langgraph.graph import StateGraph, END, START
from agentic.utils.model_loader import load_model
from agentic.prompt_library.prompt import SYSTEM_PROMPT

# Tool wrappers
from agentic.tool.firebase_tool import write_project_summary, get_dev_profiles
from agentic.tool.vector_retriever import get_vector_retriever
from agentic.tool.scrum_timer import is_scrum_time_reached
from agentic.tool.standup_fetcher import get_all_standups

# Agent helpers
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langgraph.prebuilt import ToolNode, tools_condition


class ScrumGraphBuilder:
    def __init__(self, model_provider="groq"):
        self.llm = load_model()  # load_model reads LLM_PROVIDER env
        self.system_prompt = SYSTEM_PROMPT
        
        # Set up tools
        self.tools = [
            write_project_summary,
            get_dev_profiles,
            is_scrum_time_reached,
            get_all_standups
        ]

        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)
        self.graph = None

    def agent_function(self, state: dict):
        """Agent loop: respond with tickets/logic/standup summary"""
        # Can use state["current_node"] to condition which task to do if needed
        input_messages = [{"role": "system", "content": self.system_prompt}]
        user_msg = state.get("messages", [])
        input_messages.extend(user_msg)

        response = self.llm_with_tools.invoke(input_messages)
        return {"messages": [response]}

    def store_project_context_node(self, state):
        from agentic.utils.text_splitter import split_project_markdown
        from agentic.utils.embedding import embed_documents
        from agentic.utils.firebase_client import get_firestore
        from agentic.utils.pinecone_client import init_pinecone

        docs = split_project_markdown(state["project_description"])
        vectors = embed_documents(docs)
        index = init_pinecone()
        namespace = state["project_id"]
        for i, doc in enumerate(docs):
            index.upsert(vectors=[{
                "id": f"{namespace}-{i}",
                "values": vectors[i],
                "metadata": {"text": doc.page_content}
            }], namespace=namespace)

        summary = f"This project is about: {state['project_description'][:100]}..."
        db = get_firestore()
        db.collection("projects").document(state["project_id"]).update({
            "summary": summary
        })

        state["project_summary"] = summary
        return state

    def ticket_generator_node(self, state):
        retriever = get_vector_retriever(state["project_id"])
        tools = self.tools + [retriever]

        agent = create_openai_functions_agent(self.llm, tools=tools, prompt="You are a ticket planner AI...")
        executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        result = executor.invoke({"input": f"Generate tickets for: {state['project_summary']}"})
        state["tickets"] = result.get("output", [])
        return state

    def scrum_wait_node(self, state):
        import time
        from agentic.utils.firebase_client import get_firestore
        db = get_firestore()

        cycle = state.get("scrum_cycle", 0)
        project_id = state["project_id"]
        devs = state.get("dev_profiles", [])

        waited = 0
        while waited < 5:
            standups = list(db.collection("projects")
                .document(project_id)
                .collection("standups")
                .where("cycle", "==", cycle)
                .stream())
            if len(standups) >= len(devs):
                break
            time.sleep(15)
            waited += 0.25
        return state

    def standup_summarizer_node(self, state):
        from agentic.utils.firebase_client import get_firestore
        db = get_firestore()
        cycle = state["scrum_cycle"]
        project_id = state["project_id"]
        standups = db.collection("projects").document(project_id)\
                     .collection("standups")\
                     .where("cycle", "==", cycle).stream()
        all_text = "\n".join([s.to_dict()["text"] for s in standups])
        summary = self.llm.invoke(f"Summarize standups: {all_text}").content
        state["scrum_summary"].append(summary)
        return state

    def cycle_manager_node(self, state):
        state["scrum_cycle"] += 1
        if state["scrum_cycle"] >= 3:
            state["done"] = True
        return state

    def build_graph(self):
        graph_builder = StateGraph(dict)

        graph_builder.add_node("StoreProjectContext", self.store_project_context_node)
        graph_builder.add_node("TicketGenerator", self.ticket_generator_node)
        graph_builder.add_node("ScrumWait", self.scrum_wait_node)
        graph_builder.add_node("StandupSummarizer", self.standup_summarizer_node)
        graph_builder.add_node("CycleManager", self.cycle_manager_node)
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("End", lambda x: x)

        # Entry point
        graph_builder.set_entry_point("StoreProjectContext")

        # Edges
        graph_builder.add_edge("StoreProjectContext", "TicketGenerator")
        graph_builder.add_edge("TicketGenerator", "ScrumWait")
        graph_builder.add_edge("ScrumWait", "StandupSummarizer")
        graph_builder.add_edge("StandupSummarizer", "CycleManager")

        def condition(state):
            return "End" if state.get("done", False) else "TicketGenerator"

        graph_builder.add_conditional_edges("CycleManager", condition)

        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.build_graph()
