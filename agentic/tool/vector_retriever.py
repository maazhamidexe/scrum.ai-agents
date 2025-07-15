from langchain.vectorstores import Pinecone
from langchain.embeddings import OpenAIEmbeddings
from agentic.utils.pinecone_client import init_pinecone

def get_vector_retriever(project_id: str):
    """get the vector retriever for the given project"""
    index = init_pinecone()
    return Pinecone(
        index=index,
        embedding=OpenAIEmbeddings(),
        namespace=project_id
    ).as_retriever()
