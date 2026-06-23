from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_docling import DoclingLoader
from langchain_docling.loader import ExportType
from pathlib import Path
from typing import List
from docling.chunking import HierarchicalChunker
from transformers import AutoTokenizer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_qdrant import FastEmbedSparse
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from backend.constants import COLLECTION_NAME, DENSE_EMBED_MODEL, SPARSE_EMBED_MODEL, SPARSE_EMBED_BATCH_SIZE, CLIENT, FOLDER_TO_ROLES



load_dotenv()

# Dense embeddings — semantic understanding
dense_embeddings = HuggingFaceEmbeddings(
    model_name=DENSE_EMBED_MODEL,
    model_kwargs={"device": "cpu"},      # change to "cuda" if you have a GPU
    encode_kwargs={"normalize_embeddings": True}
)

# Sparse embeddings — BM25 keyword matching (via FastEmbed)
sparse_embeddings = FastEmbedSparse(model_name=SPARSE_EMBED_MODEL, batch_size=SPARSE_EMBED_BATCH_SIZE)


def load_documents(source_dir: str = "sourcefiles") -> List[Document]:
    """
    Recursively load all PDF and Markdown files from source_dir.
    """
    source_path = Path(source_dir)

    files = [
        file for file in source_path.rglob("*")
        if file.suffix.lower() in {".pdf", ".md"}
    ]

    documents = []

    for file_path in files:
        folder = file_path.relative_to(source_path).parts[0]  # "billing", "clinical", etc.
        allowed_roles = FOLDER_TO_ROLES.get(folder, [])

        loader = DoclingLoader(
            str(file_path),
            export_type=ExportType.DOC_CHUNKS,
            chunker=HierarchicalChunker(),
        )
        docs = list(loader.lazy_load())
        for doc in docs:
            doc.metadata["folder"] = folder
            doc.metadata["allowed_roles"] = allowed_roles  # list of roles that can access this document
        documents.extend(docs)

    return documents


def covert_docling_to_langchain(documents: List[Document]) -> List[Document]:
    """
    Convert Docling chunk documents to LangChain documents.
    """
    # Documents from DoclingLoader with DOC_CHUNKS already contain chunked text.
    return [Document(page_content=doc.page_content, metadata=doc.metadata) for doc in documents]

def create_vector_store(documents: List[Document]):
    """
    Create a vector store from the given documents using both dense and sparse embeddings.
    """
    # Combine into a single vector store
    #vector_store = QdrantVectorStore.from_documents(
    #    documents,
    #    embedding=dense_embeddings,
    #    sparse_embedding=sparse_embeddings,
    #    client=CLIENT,
    #    collection_name=COLLECTION_NAME,
    #    retrieval_mode=RetrievalMode.HYBRID,  # use both dense and sparse for retrieval
    #)
    vector_store = QdrantVectorStore.from_documents(
        documents,
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        host="localhost",
        port=6333,
        collection_name=COLLECTION_NAME,
        retrieval_mode=RetrievalMode.HYBRID,
    )
    return vector_store



    
if __name__ == "__main__":
    docs = load_documents()
    print(f"Loaded {len(docs)} documents from sourcefiles/")
    langchain_docs = covert_docling_to_langchain(docs)
    print(f"Converted to {len(langchain_docs)} LangChain documents after chunking.")
    vector_store = create_vector_store(langchain_docs)
    print("Vector store created with both dense and sparse embeddings.")









