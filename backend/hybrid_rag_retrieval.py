from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from backend.data_loader import COLLECTION_NAME, dense_embeddings, sparse_embeddings
from backend.llm import llm
from langchain_qdrant import QdrantVectorStore, RetrievalMode
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from backend.constants import SYSTEM_PROMPT, RERANKER_MODEL_NAME, HYBRID_TOP_K, RERANKER_TOP_N, CLIENT
from backend.qdrant_store import get_collection_size
from typing import Dict, Any
from qdrant_client.http.models import Filter, FieldCondition, MatchValue


# Load cross-encoder model (downloads ~270MB on first run)
cross_encoder = HuggingFaceCrossEncoder(
    model_name=RERANKER_MODEL_NAME
)

# Wrap it as a LangChain document compressor
reranker = CrossEncoderReranker(
    model=cross_encoder,
    top_n=RERANKER_TOP_N           # keep only top-N after reranking
)
vector_store = QdrantVectorStore(
    client=CLIENT,
    collection_name=COLLECTION_NAME,
    embedding=dense_embeddings,
    sparse_embedding=sparse_embeddings,
    retrieval_mode=RetrievalMode.HYBRID,
)

def _build_hybrid_retriever(role: str):
    """Build a Qdrant retriever filtered by the user's allowed roles."""
    return vector_store.as_retriever(
        search_kwargs={
            "k": HYBRID_TOP_K,
            "filter": Filter(
                must=[
                    FieldCondition(
                        key="metadata.allowed_roles",
                        match=MatchValue(value=role),
                    )
                ]
            ),
        }
    )


prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{input}"),
])


def _build_reranking_chain(role: str):
    hybrid_retriever = _build_hybrid_retriever(role)
    reranking_retriever = ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=hybrid_retriever,
    )
    return create_retrieval_chain(
        reranking_retriever,
        create_stuff_documents_chain(llm, prompt),
    )


# Ask Reranking RAG a question
def ask_reranking(question: str, role: str) -> Dict[str, Any]:
    reranking_rag_chain = _build_reranking_chain(role)
    result = reranking_rag_chain.invoke({"input": question})
    
    # Convert Document objects to dicts matching Source schema
    sources = []
    for doc in result.get("context", []):
        sources.append({
            "source_document": doc.metadata.get("source_document", ""),
            "section_title": doc.metadata.get("section_title", ""),
            "collection": doc.metadata.get("collection", ""),
        })
    result["sources"] = sources
    return result

def answer_with_citations(question: str, role: str) -> Dict[str, Any]:
    "Run the RAG chain (Hybrid + Reranking + LLM answer) and return the answer along with citations."
    reranking_rag_chain = _build_reranking_chain(role)
    return reranking_rag_chain.invoke({"input": question})
