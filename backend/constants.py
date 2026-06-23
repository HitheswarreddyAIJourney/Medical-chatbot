import os
from dotenv import load_dotenv
load_dotenv()
from qdrant_client import QdrantClient
from typing import Dict, List
CLIENT = QdrantClient(host="localhost", port=6333)

# Embedding model and dimension
DENSE_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SPARSE_EMBED_MODEL = "Qdrant/bm25"
SPARSE_EMBED_BATCH_SIZE = 32

GROQ_MODEL = "openai/gpt-oss-20b"




# Prompt template
SYSTEM_PROMPT = """You are a helpful TelecomCo customer support assistant.
Answer the customer's question using ONLY the information provided in the context below.
If the answer is not in the context, say "I don't have that information."
Keep answers concise and friendly.

Context:
{context}"""

DB_PATH = os.getenv("DB_PATH", "./sourcefiles/db/mediassist.db")
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

HYBRID_TOP_K = 5
RERANKER_TOP_N = 3

COLLECTION_NAME = "medical_docs"

QDRANT_URL = "http://localhost:6333"



USERS_PATH: str = os.getenv("USERS_PATH", "./backend/data/users.json")

JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "120"))

ROLE_TO_COLLECTIONS: Dict[str, List[str]] = {
    "doctor":            ["clinical", "general"],
    "nurse":             ["nursing", "general"],
    "billing_executive": ["billing", "general"],
    "technician":        ["equipment", "general"],
    "admin":             ["clinical", "nursing", "billing", "equipment", "general"],
}

FOLDER_TO_ROLES: dict[str, list[str]] = {
    "clinical":  ["doctor", "admin"],
    "general":   ["doctor", "nurse", "billing_executive", "technician", "admin"],
    "equipment": ["technician", "admin"],
    "billing":   ["billing_executive", "admin"],
    "nursing":   ["nurse", "doctor", "admin"],
}


ALL_ROLES = set(ROLE_TO_COLLECTIONS.keys())

SQL_DB_PATH: str = os.getenv("SQL_DB_PATH", "./sourcefiles/db/mediassist.db")
SQL_RAG_ROLES = {"billing_executive", "admin"}