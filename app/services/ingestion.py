import os
from typing import Any

from flask import current_app
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".csv"}


class DocumentIngestionService:
    """Turns a file on disk into chunked LangChain Documents."""

    def _splitter(self) -> RecursiveCharacterTextSplitter:
        # Recursive splitter keeps paragraphs/sentences intact where possible,
        # which is a decent default until we layer on semantic splitters.
        return RecursiveCharacterTextSplitter(
            chunk_size=current_app.config["CHUNK_SIZE"],
            chunk_overlap=current_app.config["CHUNK_OVERLAP"],
            length_function=len,
            is_separator_regex=False,
        )

    def load_document(
        self, file_path: str, source_metadata: dict[str, Any] | None = None
    ) -> list[Any]:
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file extension: {ext!r}. "
                f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path, encoding="utf-8")

        documents = loader.load()

        for doc in documents:
            doc.metadata["source_type"] = ext
            if source_metadata:
                doc.metadata.update(source_metadata)

        return documents

    def process_and_chunk(self, file_path: str, source_url: str) -> list[Any]:
        """Load -> annotate -> split. Returns the final chunk list."""
        raw_documents = self.load_document(file_path, {"source_url": source_url})
        current_app.logger.info(
            "Loaded %d page(s)/section(s) from %s.", len(raw_documents), source_url
        )

        chunks = self._splitter().split_documents(raw_documents)
        current_app.logger.info("Split document into %d chunks.", len(chunks))
        return chunks


ingestion_service = DocumentIngestionService()
