import os
import pinecone
from dotenv import load_dotenv

load_dotenv()

def init_pinecone(index_name="project_embeddings"):
    pinecone_api_key = os.getenv("PINECONE_API_KEY")
    pinecone_env = os.getenv("PINECONE_ENV")
    pinecone.init(api_key=pinecone_api_key, environment=pinecone_env)
    return pinecone.Index(index_name)
