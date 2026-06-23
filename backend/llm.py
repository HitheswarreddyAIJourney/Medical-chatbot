import os
from langchain_groq import ChatGroq
from dotenv import load_dotenv
load_dotenv()
from backend.constants import GROQ_MODEL

llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    api_key=os.getenv("GROQ_API_KEY")
)

