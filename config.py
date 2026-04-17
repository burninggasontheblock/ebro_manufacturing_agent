import os
from dotenv import load_dotenv

load_dotenv()

# ── LLM ──────────────────────────────────────────────────────────────────────
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" | "openai"
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_MODEL: str = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o")

# ── Embeddings (OpenAI — uses OPENAI_API_KEY) ────────────────────────────────
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ── Vector store ─────────────────────────────────────────────────────────────
VECTOR_STORE_PATH: str = os.getenv("VECTOR_STORE_PATH", "./vector_store")

# ── Agent behaviour ───────────────────────────────────────────────────────────
VERBOSE: bool = os.getenv("VERBOSE", "false").lower() == "true"
MAX_AGENT_ITERATIONS: int = int(os.getenv("MAX_AGENT_ITERATIONS", "6"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "4"))


def get_llm(temperature: float = 0.0, max_tokens: int | None = None):
    """Return a configured LLM instance based on LLM_PROVIDER.

    max_tokens: optional cap on completion length. Anthropic's default (1024) is too low
    for large JSON payloads — pass a higher value (e.g. 8192) for RCA / long outputs.
    """
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        kwargs = dict(
            model=OPENAI_MODEL,
            temperature=temperature,
            api_key=OPENAI_API_KEY,
        )
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        return ChatOpenAI(**kwargs)
    from langchain_anthropic import ChatAnthropic
    kwargs = dict(
        model=ANTHROPIC_MODEL,
        temperature=temperature,
        api_key=ANTHROPIC_API_KEY,
    )
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return ChatAnthropic(**kwargs)


def get_embeddings():
    """Return OpenAI embeddings for FAISS (requires OPENAI_API_KEY)."""
    if not OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY is required for embeddings. Set it in your environment or .env."
        )
    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=OPENAI_API_KEY)
