from langchain.text_splitter import MarkdownHeaderTextSplitter

def split_project_markdown(text: str):
    splitter = MarkdownHeaderTextSplitter(headers_to_split_on=[
        ("#", "title"),
        ("##", "section")
    ])
    return splitter.split_text(text)
