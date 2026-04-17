"""
Shared RAG tool — each domain agent receives a version scoped to its category set.
"""
from langchain_core.tools import tool

from rag.knowledge_base import retrieve_as_text


def make_rag_tool(domain: str):
    """Factory: returns a @tool bound to the given domain's retriever."""

    @tool
    def search_knowledge_base(query: str) -> str:
        """
        Search the manufacturing knowledge base for KBAs, process standards,
        prior incident reports, maintenance history, and supplier records
        relevant to the query.

        Args:
            query: Natural-language search query

        Returns:
            Formatted text with top matching documents.
        """
        return retrieve_as_text(query, domain=domain, k=4)

    # Rename so agents can tell tools apart in verbose mode
    search_knowledge_base.name = f"search_knowledge_base_{domain}"
    return search_knowledge_base
