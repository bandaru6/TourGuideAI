class VectorStore:
    """ChromaDB vector store — Phase 5 implementation."""

    def __init__(self):
        pass

    async def add(self, texts: list[str], metadatas: list[dict] | None = None) -> None:
        pass

    async def query(self, query: str, k: int = 5) -> list[dict]:
        return []
