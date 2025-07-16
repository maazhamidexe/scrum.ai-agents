from langchain_huggingface import HuggingFaceEmbeddings

def embed_documents(docs):
    """
    Embed documents using HuggingFace embeddings.
    
    Args:
        docs (List[Document]): A list of documents, each having a `page_content` attribute.
    
    Returns:
        List[List[float]]: A list of embeddings for each document.
    """
    embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # Each document is expected to have a 'page_content' attribute
    return embedder.embed_documents([d.page_content for d in docs])
