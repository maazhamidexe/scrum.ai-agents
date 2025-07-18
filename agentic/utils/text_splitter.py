import re
from langchain.schema import Document

def split_project_markdown(text: str):
    # Split text into sentences using regex
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    # Create a Document for each sentence
    docs = [Document(page_content=sentence) for sentence in sentences if sentence.strip()]
    return docs
