"""
Main API server for the medical chatbot.
Endpoints:
- POST /login: Authenticate user and issue JWT token.
- GET /collections/{role}: Get accessible collections for a given role.
- GET /health: Health check endpoint.


"""

import logging
from fastapi import FastAPI, HTTPException, status, Depends
from dotenv import load_dotenv
import uuid
import os
import time
from inngest.experimental import ai
from contextlib import asynccontextmanager
from .schema import HealthResponse, LoginRequest, LoginResponse, CollectionsResponse, ChatRequest, ChatResponse, Source
from .auth import authenticate, issue_token,UserRecord, get_current_user
from .constants import ALL_ROLES, ROLE_TO_COLLECTIONS, SQL_RAG_ROLES, SQL_DB_PATH
from fastapi.middleware.cors import CORSMiddleware
from .router import classify_question
from .sql_rag_retrieval import sql_rag_chain
from .hybrid_rag_retrieval import ask_reranking, reranker
from .data_loader import dense_embeddings, sparse_embeddings

log = logging.getLogger("medibot")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Booting MediBot…")
    from .constants import QDRANT_URL
    from qdrant_client import QdrantClient
    try:
        client = QdrantClient(url=QDRANT_URL, timeout=10.0)
        # Force a round trip so a down Qdrant fails fast at boot, not on first /chat.
        client.get_collections()
    except Exception as e:
        mode = f"server at {QDRANT_URL}"
        log.error(
            "Cannot reach Qdrant (%s): %s\n"
            "  • Docker:    docker run -d --name medibot-qdrant -p 6333:6333 qdrant/qdrant\n"
            "  • Verify:    curl http://localhost:6333/healthz",
            mode, e,
        )
        raise

    # Warm up models in the background-ish (synchronous but once).
    try:
        log.info("Warming up models…")
        reranker
        dense_embeddings
        sparse_embeddings
    except Exception as e:
        log.warning("Model warm-up failed: %s — first /chat will load them.", e)

    log.info("MediBot ready.")
    yield
    log.info("MediBot shutting down.")

app = FastAPI(
    title="Medical Chatbot API",
    description="API for a medical chatbot that provides health advice and information.",
    version="1.0.0",
    lifespan= lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
)

# ---------- Endpoints ----------

@app.get("/collections/{role}", response_model=CollectionsResponse)
def get_collections(role: str) -> CollectionsResponse:
    if role not in ALL_ROLES:
        raise HTTPException(status_code=404, detail=f"Unknown role '{role}'")
    return CollectionsResponse(role=role, collections=ROLE_TO_COLLECTIONS[role])

@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", version="1.0.0")

@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest) -> LoginResponse:
    user = authenticate(req.username, req.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    token = issue_token(user.username, user.role)
    return LoginResponse(token=token, role=user.role, username=user.username)

def _rbac_refusal(role: str, hint: str = "") -> str:
    accessible = ROLE_TO_COLLECTIONS[role]
    coll_str = ", ".join(accessible)
    base = (
        f"Access restricted: as a '{role}', you do not have permission to retrieve "
        f"this content. I can only answer questions from the {coll_str} collection(s). "
        f"Please contact the admin team if you believe this is an error."
    )
    if hint:
        base = f"{hint}  {base}"
    return base


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: UserRecord = Depends(get_current_user)) -> ChatResponse:
    t0 = time.time()
    role = user.role
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Empty question")

    route = classify_question(question, role)
    log.info("[chat] role=%s route=%s q=%r", role, route, question[:80])

    # SQL RAG path — only for permitted roles.
    if route == "sql" and role in SQL_RAG_ROLES:
        try:
            result = sql_rag_chain(question, SQL_DB_PATH)
        except Exception as e:
            log.exception("SQL RAG failed: %s", e)
            raise HTTPException(status_code=500, detail=f"SQL RAG error: {e}")
        result["role"] = role
        return ChatResponse(
            answer=result["answer"],
            sources=[Source(**s) for s in result["sources"]],
            retrieval_type="sql_rag",
            role=role,
        )

    # Hybrid RAG path.
    try:
        result = ask_reranking(question,role)
        #result = rag.answer_with_citations(question, role)
    except Exception as e:
        log.exception("Hybrid RAG failed: %s", e)
        # Surface the most common Qdrant-down / empty-store failure modes in
        # the response body so a 500 is debuggable from the browser.
        msg = str(e)
        if "not found" in msg.lower() and "collection" in msg.lower():
            detail = (
                f"{msg}. Did you run `python scripts/ingest.py`? "
                f"With QDRANT_IN_MEMORY=1, ingest and serve must run in the "
                f"same process — use `python scripts/serve.py`."
            )
        elif "timed out" in msg.lower() or "connection" in msg.lower():
            detail = (
                f"Qdrant is unreachable: {msg}. "
                f"Start the container (docker run …) or set QDRANT_IN_MEMORY=1 "
                f"and use `python scripts/serve.py`."
            )
        else:
            detail = f"Hybrid RAG error: {e}"
        raise HTTPException(status_code=500, detail=detail)

    # RBAC refusal: zero results means the role's filter excluded
    # everything relevant. Return a clean refusal without calling the LLM
    # — otherwise it would hallucinate on empty context.
    if not result["answer"] and not result["sources"]:
        refusal = _rbac_refusal(role, hint="I could not find an answer within your authorised collections.")
        log.info("[chat] rbac_refusal role=%s elapsed=%.2fs", role, time.time() - t0)
        return ChatResponse(
            answer=refusal,
            sources=[],
            retrieval_type="hybrid_rag",
            role=role,
        )

    log.info("[chat] hybrid_ok role=%s elapsed=%.2fs sources=%d",
             role, time.time() - t0, len(result["sources"]))
    return ChatResponse(
        answer=result["answer"],
        sources=[Source(**s) for s in result["sources"]],
        retrieval_type="hybrid_rag",
        role=role,
    )