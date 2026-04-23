import os
from typing import Any

from flask import current_app
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings


class VectorDBService:
    """
    Thin wrapper over LangChain's Chroma integration.

    Two modes depending on config:
      * `CHROMA_HOST` set  -> connect to a Chroma server over HTTP
                              (this is how docker-compose runs).
      * otherwise          -> embedded persistent client writing to disk.
    """

    def __init__(self) -> None:
        self._vector_store: Chroma | None = None
        self._embeddings: OpenAIEmbeddings | None = None

    # --- lazy init so we only touch network/disk when actually used ----------

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        if self._embeddings is None:
            self._embeddings = OpenAIEmbeddings(
                model=current_app.config["OPENAI_EMBEDDING_MODEL"],
                api_key=current_app.config.get("OPENAI_API_KEY"),
            )
        return self._embeddings

    @property
    def vector_store(self) -> Chroma:
        if self._vector_store is not None:
            return self._vector_store

        collection = current_app.config["CHROMA_COLLECTION"]
        chroma_host = current_app.config.get("CHROMA_HOST")

        if chroma_host:
            # Server mode: talk to the standalone Chroma container.
            import chromadb

            client = chromadb.HttpClient(
                host=chroma_host,
                port=current_app.config["CHROMA_PORT"],
            )
            current_app.logger.info(
                "Using Chroma HTTP client at %s:%s (collection=%s)",
                chroma_host,
                current_app.config["CHROMA_PORT"],
                collection,
            )
            self._vector_store = Chroma(
                client=client,
                collection_name=collection,
                embedding_function=self.embeddings,
            )
        else:
            # Embedded mode: persist to local disk.
            persist_dir = current_app.config["CHROMA_DB_DIR"]
            os.makedirs(persist_dir, exist_ok=True)
            current_app.logger.info(
                "Using embedded Chroma at %s (collection=%s)", persist_dir, collection
            )
            self._vector_store = Chroma(
                collection_name=collection,
                embedding_function=self.embeddings,
                persist_directory=persist_dir,
            )

        return self._vector_store

    # --- public API ----------------------------------------------------------

    def store_documents(self, chunks: list[Any]) -> bool:
        if not chunks:
            current_app.logger.warning("store_documents called with no chunks; skipping.")
            return False

        current_app.logger.info("Storing %d chunks into Chroma...", len(chunks))
        ids = self.vector_store.add_documents(documents=chunks)
        current_app.logger.info("Successfully stored %d chunks.", len(ids))
        return True

    def get_retriever(self, search_kwargs: dict | None = None):
        if search_kwargs is None:
            search_kwargs = {"k": current_app.config.get("RETRIEVAL_K", 4)}
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def collection_stats(self) -> dict:
        """Small helper used by the /stats endpoint and tests."""
        try:
            count = self.vector_store._collection.count()  # noqa: SLF001
        except Exception:  # pragma: no cover - defensive; client may be down
            count = None
        return {
            "collection": current_app.config["CHROMA_COLLECTION"],
            "document_count": count,
        }


vector_db_service = VectorDBService()
