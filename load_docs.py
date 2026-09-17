import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

docs_folder = "docs"
all_pages = []

for filename in os.listdir(docs_folder):
    if filename.endswith(".pdf"):
        path = os.path.join(docs_folder, filename)
        loader = PyPDFLoader(path)
        pages = loader.load()
        all_pages.extend(pages)
        print(f"Loaded {filename}: {len(pages)} pages")

print(f"\nTotal pages loaded: {len(all_pages)}")

splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
chunks = splitter.split_documents(all_pages)

print(f"Total chunks created: {len(chunks)}")
print("\n--- Sample chunk ---")
print(chunks[0].page_content[:300])
