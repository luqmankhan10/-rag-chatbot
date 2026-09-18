# RAG Chatbot

A Retrieval-Augmented Generation (RAG) chatbot that answers questions over PDF and company documents, built with LangChain, FAISS/Chroma vector search, and Streamlit.

## Features
- Ingests and indexes PDF/company documents
- Semantic retrieval over document chunks using vector search
- Conversational Q&A interface powered by an LLM
- Simple Streamlit web UI

## Tech Stack
- **LangChain** — RAG pipeline orchestration
- **FAISS / Chroma** — vector store for semantic search
- **Streamlit** — frontend UI
- **OpenAI / OpenRouter API** — LLM backend

## Project Structure

## Setup

1. Clone the repo
```bash
   git clone https://github.com/luqmankhan10/-rag-chatbot.git
   cd -rag-chatbot
```

2. Install dependencies
```bash
   pip install -r requirements.txt
```

3. Set up environment variables
```bash
   cp .env.example .env
   # then edit .env and add your API key(s)
```

4. Build the vector index
```bash
   python build_index.py
```

5. Run the app
```bash
   streamlit run streamlit_app.py
```

## Usage
Upload or place your PDF/company documents in the `docs/` folder, rebuild the index, then ask questions through the Streamlit chat interface.

## License
MIT
