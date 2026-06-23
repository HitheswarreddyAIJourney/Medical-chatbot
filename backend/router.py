import re
from typing import Literal


# Phrases that strongly imply a numbers/aggregate question.
_NUMERIC_KEYWORDS = re.compile(
    r"\b("
    r"count|how many|total|sum|average|avg|min|max|"
    r"top\s+\d|most|least|breakdown|percentage|"
    r"per\s+(month|week|day|department|category|insurer|campus|equipment|claim)|"
    r"by\s+(department|category|insurer|campus|equipment|status|month|week|day|insurer)"
    r")\b",
    re.IGNORECASE,
)

# Substantive words that should also appear to count as "analytical" intent.
_ANALYTICAL_TOPICS = re.compile(
    r"\b("
    r"claim|claims|ticket|tickets|maintenance|equipment|insurer|insurers|"
    r"department|departments|patient|category|categories|campus|"
    r"status|approved|rejected|pending|escalated|resolved|open|in[_ ]progress|"
    r"amount|amounts|amounted|valued|valued at"
    r")\b",
    re.IGNORECASE,
)


def classify_question(question: str, role: str) -> Literal["sql", "hybrid"]:
    """Return "sql" if the question looks like an analytical numbers query,
    else "hybrid".

    The role gate is NOT enforced here — the caller is responsible for
    refusing SQL RAG for non-permitted roles.
    """
    if _NUMERIC_KEYWORDS.search(question) and _ANALYTICAL_TOPICS.search(question):
        return "sql"
    return "hybrid"