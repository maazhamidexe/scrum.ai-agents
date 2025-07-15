import os
from dotenv import load_dotenv

# LangChain LLM wrappers
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama

load_dotenv()

def load_model():
    """
    Load LLM from Groq or Ollama based on environment config.
    Returns a LangChain-compatible chat model.
    """
    provider = "groq"

    if provider == "groq":
        groq_api_key = os.getenv("GROQ_API_KEY")
        groq_model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        print(f"🔌 Loading Groq model: {groq_model}")
        return ChatGroq(
            model_name=groq_model,
            temperature=0.2,
            api_key=groq_api_key
        )

    elif provider == "ollama":
        ollama_model = os.getenv("OLLAMA_MODEL", "deepseek-coder:14b-instruct-fp16")
        print(f"💻 Loading Ollama model: {ollama_model}")
        return ChatOllama(
            model=ollama_model,
            temperature=0.2
        )

    else:
        raise ValueError(f"Unknown LLM provider: {provider}")
