from __future__ import annotations

from typing import Any

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from app.config import DATA_DIR, TOP_K, VECTOR_STORE_DIR
from app.services.embeddings import get_embeddings

INDEX_PATH = VECTOR_STORE_DIR / "faiss_index"


def chunk_documents(chunks: list[dict[str, Any]]) -> list[Document]:
    """Convert stored chunk dictionaries into LangChain documents for FAISS indexing."""
    documents: list[Document] = []
    for chunk in chunks:
        text = str(chunk.get("text", "")).strip()
        if not text:
            continue
        documents.append(
            Document(
                page_content=text,
                metadata={
                    "document_id": chunk.get("document_id"),
                    "chunk_id": chunk.get("chunk_id"),
                    "source": chunk.get("source"),
                    "page": chunk.get("page"),
                },
            )
        )
    return documents


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

    embeddings = get_embeddings()
    vector_store = FAISS.from_documents(chunks, embeddings)
    vector_store.save_local(str(INDEX_PATH))

    return {"chunks": len(chunks), "path": str(INDEX_PATH)}


def index_uploaded_chunks(chunks: list[dict[str, Any]]) -> dict[str, Any]:
    """Persist the provided document chunks in the local FAISS index."""
    documents = chunk_documents(chunks)
    if not documents:
        return {"chunks": 0, "path": str(INDEX_PATH)}

    VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
    embeddings = get_embeddings()
    if INDEX_PATH.exists():
        vector_store = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
        vector_store.add_documents(documents)
    else:
        vector_store = FAISS.from_documents(documents, embeddings)
    vector_store.save_local(str(INDEX_PATH))
    return {"chunks": len(documents), "path": str(INDEX_PATH)}


def query_documents(query: str, k: int = TOP_K) -> dict[str, Any]:
    """Search the local FAISS index for the most relevant document chunks."""
    if not INDEX_PATH.exists():
        return {"query": query, "results": []}

    embeddings = get_embeddings()
    vector_store = FAISS.load_local(str(INDEX_PATH), embeddings, allow_dangerous_deserialization=True)
    docs = vector_store.similarity_search(query, k=k)

    return {
        "query": query,
        "results": [{"page_content": doc.page_content, "metadata": doc.metadata} for doc in docs],
    }
