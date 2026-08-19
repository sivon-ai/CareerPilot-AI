from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from app.config import DATA_DIR, EMBEDDING_MODEL, OPENAI_API_KEY

INDEX_PATH = DATA_DIR / "faiss_index"


def _ensure_embeddings() -> Any:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is not configured. Add it to backend/.env")
    return OpenAIEmbeddings(model=EMBEDDING_MODEL, openai_api_key=OPENAI_API_KEY)


def build_document_index(file_obj: Any, filename: str) -> dict[str, Any]:
    """Load a document from upload, split it, and persist a vector index."""
    if not filename.lower().endswith(".pdf"):
        raise ValueError("Only PDF files are supported at the moment.")

    temp_path = DATA_DIR / filename
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    with open(temp_path, "wb") as destination:
        destination.write(file_obj.read())

    loader = PyPDFLoader(str(temp_path))
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks = splitter.split_documents(documents)

    embeddings = _ensure_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(str(INDEX_PATH))

    return {"chunks": len(chunks), "path": str(INDEX_PATH)}


def query_documents(query: str) -> dict[str, Any]:
    """Search the local FAISS index for the most relevant document chunks."""
    if not INDEX_PATH.exists():
        return {"query": query, "results": []}

    embeddings = _ensure_embeddings()
    vector_store = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    docs = vector_store.similarity_search(query, k=5)

    return {
        "query": query,
        "results": [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs],
    }
