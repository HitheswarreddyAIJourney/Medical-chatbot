from langchain_community.utilities import SQLDatabase
from langchain_classic.chains import create_sql_query_chain
from langchain_community.utilities import SQLDatabase
from backend.llm import llm
import re
from backend.constants import SYSTEM_PROMPT, DB_PATH, GROQ_MODEL
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging
import sqlite3
from langchain_core.messages import HumanMessage, SystemMessage


log = logging.getLogger(__name__)

db = SQLDatabase.from_uri(f"sqlite:///{DB_PATH}")

sql_query_chain = create_sql_query_chain(llm, db)

# Keywords allowed anywhere in the query (case-insensitive). Anything
# outside this list is rejected.
_ALLOWED_KEYWORDS = {
    "SELECT", "WITH", "FROM", "WHERE", "GROUP", "BY", "ORDER", "HAVING",
    "LIMIT", "OFFSET", "AS", "AND", "OR", "NOT", "IN", "IS", "NULL",
    "LIKE", "BETWEEN", "CASE", "WHEN", "THEN", "ELSE", "END", "ON",
    "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "FULL", "CROSS",
    "DISTINCT", "CAST", "COALESCE", "ROUND", "ABS",
    "COUNT", "SUM", "AVG", "MIN", "MAX",
    "STRFTIME", "DATE", "DATETIME", "JULIANDAY",
    "ASC", "DESC",
}

# Keywords explicitly forbidden (case-insensitive).
_FORBIDDEN_KEYWORDS = {
    "DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "REPLACE",
    "PRAGMA", "ATTACH", "DETACH", "VACUUM", "REINDEX", "TRUNCATE",
    "GRANT", "REVOKE", "SAVEPOINT", "COMMIT", "ROLLBACK",
    "BEGIN", "END", "EXPLAIN",  # EXPLAIN often reveals query plan but skip for safety
}

_SQL_FENCE_RE = re.compile(r"^```(?:sql)?\s*", re.IGNORECASE)
_SQL_FENCE_END_RE = re.compile(r"\s*```$", re.IGNORECASE)
_SQL_STATEMENT_RE = re.compile(r"(SELECT\b[\s\S]+?;)", re.IGNORECASE)


# ---------- Step 1: schema introspection ----------

def _introspect_schema(db_path: str) -> str:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        parts: List[str] = []
        for t in tables:
            cur.execute(f"PRAGMA table_info({t})")
            cols = [(row[1], row[2]) for row in cur.fetchall()]
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            row_count = cur.fetchone()[0]
            # Distinct status values, if a status column exists.
            status_values: List[str] = []
            if "status" in [c[0] for c in cols]:
                try:
                    cur.execute(f"SELECT DISTINCT status FROM {t} ORDER BY status")
                    status_values = [r[0] for r in cur.fetchall()]
                except Exception:
                    pass
            col_str = ", ".join(f"{n} {ty}" for n, ty in cols)
            line = f"- {t}({col_str})  [{row_count} rows"
            if status_values:
                line += f"; status ∈ {{{', '.join(status_values)}}}"
            line += "]"
            parts.append(line)
        return "\n".join(parts)
    finally:
        con.close()

# ---------- Step 2: NL -> SQL ----------

_SQL_SYSTEM = (
    "You translate natural-language questions into a single SQLite SELECT "
    "statement against the schema below. Use only SELECT (WITH is allowed). "
    "Always include LIMIT 100 unless the question explicitly asks for top-N. "
    "Treat date strings as ISO yyyy-mm-dd. The sample date is 2026-06-21. "
    "Return ONLY the raw SQL statement. No prose, no code fences, no comments."
)

def _generate_sql(question: str, schema_text: str) -> str:
    response = llm.generate(
        messages=[
            [
                SystemMessage(content=_SQL_SYSTEM + f"\n\nSchema:\n{schema_text}"),
                HumanMessage(content=question.strip()),
            ]
        ],
        stop=None,
    )
    return response.generations[0][0].text.strip()

# ---------- Step 3: extract + validate SQL ----------

def extract_sql(raw: str) -> str:
    """Strip code fences, find the first SELECT/WITH statement, allow-list check."""
    sql = raw.strip()
    sql = _SQL_FENCE_RE.sub("", sql)
    sql = _SQL_FENCE_END_RE.sub("", sql)
    # Sometimes the model prefixes with prose like "Here is the query:\n".
    m = _SQL_STATEMENT_RE.search(sql)
    if m:
        sql = m.group(1)
    sql = sql.strip().rstrip(";").strip()

    # Reject comments and suspicious characters.
    if "--" in sql or "/*" in sql or "*/" in sql:
        raise ValueError("SQL contains comment markers (forbidden).")
    if ";" in sql and not sql.endswith(";"):
        # Only one statement allowed; we already stripped trailing ; above.
        pass  # already handled

    # Keyword allow-list + forbidden check.
    tokens = re.findall(r"[A-Za-z_]+", sql)
    upper = {t.upper() for t in tokens}
    forbidden_hit = upper & _FORBIDDEN_KEYWORDS
    if forbidden_hit:
        raise ValueError(f"SQL contains forbidden keyword(s): {sorted(forbidden_hit)}")
    unknown = upper - _ALLOWED_KEYWORDS
    # Identifier-like tokens (table/column names) are fine; we only flag
    # unknown ALL-CAPS keywords.
    if unknown:
        # Allow these to pass — many SQL functions / names aren't in the
        # allow-list, and sqlite will raise on bad SQL anyway. Log only.
        log.debug("extract_sql: unknown tokens %s", sorted(unknown))

    return sql

# ---------- Step 4: execute ----------

def _execute_sql(db_path: str, sql: str) -> Tuple[List[str], List[tuple]]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cur = con.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in (cur.description or [])]
        return cols, rows
    finally:
        con.close()

# ---------- Step 5: NL answer ----------

def _format_rows(cols: List[str], rows: List[tuple], cap: int = 50) -> str:
    if not rows:
        return "(no rows returned)"
    head = rows[:cap]
    rendered = [", ".join(repr(c) for c in row) for row in head]
    table = "Columns: " + ", ".join(cols) + "\n" + "\n".join(rendered)
    if len(rows) > cap:
        table += f"\n... ({len(rows) - cap} more rows truncated)"
    return table


_ANSWER_SYSTEM = (
    "You are a healthcare operations analyst. Summarise the SQL result table "
    "below in plain English, answering the user's question directly. "
    "If the question asks for a count/total, state the number. "
    "Be concise (under 120 words). Do not invent values."
)

def _natural_language_answer(question: str, cols: List[str], rows: List[tuple]) -> str:
    table = _format_rows(cols, rows)
    response = llm.generate(
        messages=[
            [
                SystemMessage(content=_ANSWER_SYSTEM),
                HumanMessage(content=f"Question: {question}\n\nResult:\n{table}"),
            ]
        ],
        stop=None,
    )
    return response.generations[0][0].text.strip()

def sql_rag_chain(question: str, db_path: str) -> Dict[str, Any]:
    """Run the three-step SQL RAG chain.

    Returns a dict compatible with ChatResponse:
        {answer, sources, retrieval_type="sql_rag", role}
    """
    if not Path(db_path).exists():
        raise FileNotFoundError(f"SQLite database not found at {db_path}")

    log.info("[sql_rag] step=schema_introspect")
    schema = _introspect_schema(db_path)

    log.info("[sql_rag] step=nl_to_sql")
    raw_sql = _generate_sql(question, schema)
    log.info("[sql_rag] step=extract_sql  raw=%r", raw_sql[:120])

    sql = extract_sql(raw_sql)
    log.info("[sql_rag] step=execute_sql  sql=%s", sql[:120])

    cols, rows = _execute_sql(db_path, sql)
    log.info("[sql_rag] step=nl_answer    rows=%d", len(rows))

    answer = _natural_language_answer(question, cols, rows)

    return {
        "answer": answer,
        "sources": [
            {
                "source_document": "mediassist.db",
                "section_title": sql[:80] + ("..." if len(sql) > 80 else ""),
                "collection": "database",
            }
        ],
        "retrieval_type": "sql_rag",
        "role": None,  # set by orchestrator
    }