import os
from pinecone import Pinecone, ServerlessSpec

def init_pinecone(index_name="projectembeddings"):
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pc = Pinecone(api_key=pinecone_api_key)
    # Check if index exists, if not create it
    if index_name not in pc.list_indexes().names():
        pc.create_index(
            name=index_name,
            dimension=384,  # MiniLM dimension
            metric='cosine'
        )
    return pc.Index(index_name)
