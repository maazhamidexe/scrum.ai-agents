import warnings
from langchain_pinecone import Pinecone
from langchain_huggingface import HuggingFaceEmbeddings
from agentic.utils.pinecone_client import init_pinecone

def get_vector_retriever(project_id: str):
    """get the vector retriever for the given project"""
    # Suppress Pinecone LangChainDeprecationWarning
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, message=".*Pinecone.*deprecated.*")
        warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*Pinecone.*deprecated.*")
        index = init_pinecone()  # This is a Pinecone Index object
        return Pinecone(
            index=index,
            embedding=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2"),
            text_key="text",  # Required parameter for the new API
            namespace=project_id
        ).as_retriever()
